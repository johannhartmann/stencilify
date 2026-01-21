# Test Workflow

## 1. Bilder hinzufügen

Lege deine Test-Bilder in `test_examples/` ab:
- `batman_kid.jpg`
- `supergirl_kid.jpg`
- etc.

```bash
# Beispiel: Commit der Bilder
git add test_examples/*.jpg
git commit -m "Add test images"
git push
```

## 2. Tests ausführen

```bash
# Alle Tests auf einmal
./test_examples/run_tests.sh

# Oder einzeln für ein Bild
uv run stencilify generate test_examples/batman_kid.jpg \
  --palette "#000000" --palette "#808080" --palette "#ffffff" \
  --layer-mode overlapping \
  --outdir test_examples/output_batman_overlapping
```

## 3. Ergebnisse bewerten

```bash
# Automatische Analyse
uv run python test_examples/evaluate_results.py
```

## 4. Ergebnisse anschauen

Die generierten Stencils findest du in:
- `test_examples/output_*_knockout/` - Knockout-Modus
- `test_examples/output_*_overlapping/` - Overlapping-Modus

Jedes Verzeichnis enthält:
- `01_*.png`, `02_*.png`, `03_*.png` - Layer-Masken
- `*.svg` - Vektorversionen für Lasercutter
- `preview.png` - Vorschau aller Layer
- `report.json` - Detaillierte Metriken

## Was zu bewerten ist

### Automatische Maskenerkennung
- ✓ Wird der Hintergrund korrekt entfernt?
- ✓ Bleibt das komplette Subjekt erhalten?
- ✓ Sind die Ränder sauber?

### Layer-Qualität
- ✓ Sind die Farben sinnvoll getrennt?
- ✓ Sind Details erkennbar (Logos, Gesichter)?
- ✓ Gibt es zu viele "Islands" (schwebende Teile)?

### Overlapping-Modus
- ✓ Layer 1 (dunkelste) hat volle Silhouette?
- ✓ Layer 2 ist kleiner als Layer 1?
- ✓ Layer 3 ist kleiner als Layer 2?
- ✓ Registrierungsmarken in allen 4 Ecken?
- ✓ Solide Ränder um jede Layer?
