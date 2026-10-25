<?php
/* Teller van telonline.org (v3.37)
   ---------------------------------------------------------------------------
   Jay: "De echte wens is dat er op de voorpagina van telonline.org "Al 253
   tellingen gedaan"." En: "Dan dus een kleine eigen teller op de server. We
   staan op 409 tellingen op dit moment."

   GET  /teller/          {"tellingen": N}
   POST /teller/  h=<64 hex>
        Een vingerafdruk van één telling: de SHA-256 van de naam van de ZIP met
        een vast voorvoegsel (blok "teller" in de vijf veld-apps). Nieuw? Dan
        telt hij mee. Elke vingerafdruk telt één keer, dus twee keer opslaan of
        doortellen telt niet dubbel. Antwoord: {"tellingen": N, "nieuw": bool}.

   Bewaard wordt alleen de lijst vingerafdrukken (gezien.txt, één regel van 64
   tekens per telling, dus het aantal = BEGIN + bestandsgrootte / 65) en de
   tijden van de laatste nieuwe (recent.txt, voor de rem). Geen IP-adressen,
   geen andere gegevens. Het serverlog van de hostingprovider staat hier los van.

   Opslag: buiten de webmap, standaard twee mappen boven dit bestand
   (/var/www/vhosts/telonline.org/teller-data in Plesk), of TELLER_MAP. Ligt de
   opslag toch in de webmap, dan weigert de teller (503) in plaats van de lijst
   op straat te leggen. Een nieuwe release overschrijft hem niet: hij staat niet
   in de repo.                                                                */
declare(strict_types=1);

const BEGIN = 409;            // Jay, 25-10-2026: "We staan op 409 tellingen op dit moment."
const REGEL = 65;             // 64 hex + "\n"

$maxPerUur = (int)(getenv('TELLER_MAX_PER_UUR') ?: 60);   // rem tegen opdrijven; de test zet hem lager
$map = getenv('TELLER_MAP') ?: dirname(__DIR__, 2) . '/teller-data';

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

function antwoord(int $code, array $data): void
{
    http_response_code($code);
    echo json_encode($data), "\n";
    exit;
}

if (!is_dir($map) && !@mkdir($map, 0750, true)) {
    antwoord(503, ['fout' => 'de opslag van de teller is er niet']);
}
$echt = realpath($map);
$web = realpath($_SERVER['DOCUMENT_ROOT'] ?? '') ?: null;
if ($echt === false || ($web !== null && strpos($echt . '/', rtrim($web, '/') . '/') === 0)) {
    antwoord(503, ['fout' => 'de opslag van de teller ligt in de webmap; zet TELLER_MAP']);
}
$gezien = $echt . '/gezien.txt';
$recent = $echt . '/recent.txt';

function aantalUit(int $bytes): int
{
    return BEGIN + intdiv($bytes, REGEL);
}

$methode = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($methode === 'GET' || $methode === 'HEAD') {
    clearstatcache(true, $gezien);
    header('Cache-Control: public, max-age=60');
    antwoord(200, ['tellingen' => aantalUit(is_file($gezien) ? (int)filesize($gezien) : 0)]);
}
if ($methode !== 'POST') {
    header('Allow: GET, POST');
    antwoord(405, ['fout' => 'alleen GET en POST']);
}
header('Cache-Control: no-store');

$h = strtolower(trim((string)($_POST['h'] ?? '')));
if (!preg_match('/^[0-9a-f]{64}$/', $h)) {
    antwoord(400, ['fout' => 'geen geldige vingerafdruk']);
}

$fp = @fopen($gezien, 'c+');
if ($fp === false) {
    antwoord(503, ['fout' => 'de teller kan niet schrijven']);
}
flock($fp, LOCK_EX);                       // één tegelijk: het tellen klopt ook bij drukte
$inhoud = stream_get_contents($fp);
$voor = strlen($inhoud);
if (strpos($inhoud, $h . "\n") !== false) {   // elke regel is precies 64 tekens + "\n"
    flock($fp, LOCK_UN);
    fclose($fp);
    antwoord(200, ['tellingen' => aantalUit($voor), 'nieuw' => false]);
}

// De rem: hooguit $maxPerUur nieuwe tellingen in het laatste uur.
$nu = time();
$tijden = is_file($recent) ? array_values(array_filter(array_map('intval', file($recent, FILE_IGNORE_NEW_LINES)),
    function ($t) use ($nu) { return $t > $nu - 3600; })) : [];
if (count($tijden) >= $maxPerUur) {
    flock($fp, LOCK_UN);
    fclose($fp);
    header('Retry-After: 3600');
    antwoord(429, ['fout' => 'even te veel nieuwe tellingen; later opnieuw', 'tellingen' => aantalUit($voor)]);
}

fseek($fp, 0, SEEK_END);
fwrite($fp, $h . "\n");
fflush($fp);
$tijden[] = $nu;
file_put_contents($recent, implode("\n", $tijden) . "\n");
flock($fp, LOCK_UN);
fclose($fp);
antwoord(200, ['tellingen' => aantalUit($voor + REGEL), 'nieuw' => true]);
