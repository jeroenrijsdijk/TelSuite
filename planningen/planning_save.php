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
if (!$raw) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Geen data ontvangen']);
    exit;
}

$data = json_decode($raw, true);
if (!$data) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Ongeldige JSON']);
    exit;
}

// Bestandsnaam afleiden uit sessie_naam + datum
$naam  = preg_replace('/[^a-zA-Z0-9_\- ]/', '', $data['sessie_naam'] ?? 'planning');
$naam  = preg_replace('/\s+/', '_', strtolower(trim($naam)));
$datum = preg_replace('/[^0-9\-]/', '', $data['datum'] ?? date('Y-m-d'));
$bestand = 'planning_' . $naam . '_' . $datum . '.json';

$pad = __DIR__ . '/' . $bestand;

if (file_put_contents($pad, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)) === false) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'Opslaan mislukt']);
    exit;
}

echo json_encode(['ok' => true, 'bestand' => $bestand]);
