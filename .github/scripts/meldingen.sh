#!/bin/bash
# Voor tests.yml: zet de FOUT-regels van een mislukte test als melding
# (annotation) bij de controle op GitHub. Dan zie je in de PR wat er misging,
# zonder het hele log te openen. GitHub toont er hooguit tien per stap.
#   meldingen.sh <testnaam> <uitvoerbestand>
naam="$1"; uit="$2"
[ -f "$uit" ] || { echo "::error title=$naam::geen uitvoer gevonden"; exit 0; }
esc() { sed -e 's/%/%25/g' -e 's/\r/%0D/g'; }
fouten=$(grep -E '^\s*FOUT|Error|Traceback|Timeout' "$uit" | head -9)
if [ -n "$fouten" ]; then
  while IFS= read -r r; do echo "::error title=$naam::$(printf '%s' "$r" | esc)"; done <<< "$fouten"
fi
# de laatste regel: de telling (of het einde van een traceback)
echo "::error title=$naam (einde)::$(tail -n 1 "$uit" | esc)"
