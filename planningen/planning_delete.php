<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Method not allowed']);
    exit;
}

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!$data || !isset($data['bestand'])) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Geen bestand opgegeven']);
    exit;
}

$bestand = $data['bestand'];

// Strikte naamvalidatie — voorkomt pad-traversal en willekeurige bestanden verwijderen.
// Alleen 'planning_<naam>.json' met veilige tekens in <naam>.
if (!preg_match('/^planning_[a-zA-Z0-9_\-]+\.json$/', $bestand)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Ongeldige bestandsnaam']);
    exit;
}

$pad = __DIR__ . '/' . $bestand;

// realpath check als extra borging tegen symlink-trucs
$real = realpath($pad);
if ($real === false || dirname($real) !== __DIR__) {
    http_response_code(404);
    echo json_encode(['ok' => false, 'error' => 'Bestand niet gevonden']);
    exit;
}

if (!unlink($real)) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'Verwijderen mislukt']);
    exit;
}

echo json_encode(['ok' => true]);
