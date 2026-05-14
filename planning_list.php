<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$dir = __DIR__;
$files = glob($dir . '/planning_*.json');
$result = [];

foreach ($files as $file) {
    $raw = file_get_contents($file);
    $data = json_decode($raw, true);
    if (!$data) continue;

    $result[] = [
        'bestand'     => basename($file),
        'sessie_naam' => $data['sessie_naam'] ?? basename($file),
        'datum'       => $data['datum']       ?? '',
        'tijdstip'    => $data['tijdstip']    ?? '',
        'teller'      => $data['teller']      ?? '',
        'tel_type'    => $data['tel_type']    ?? 'auto',
        'n_wegen'     => $data['n_wegen']     ?? 0,
        'aangemaakt'  => $data['aangemaakt']  ?? '',
    ];
}

// Sorteren op datum + aangemaakt (nieuwste eerst)
usort($result, function($a, $b) {
    $da = $a['datum'] . $a['aangemaakt'];
    $db = $b['datum'] . $b['aangemaakt'];
    return strcmp($db, $da);
});

echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
