$output = "d:\SmartChef\cod_complet.txt"
$separator = "---------"

$descs = @{}
$descs["backend\app.py"] = "Serverul principal FastAPI - defineste endpoint-urile REST pentru retete, nutritie si health check, plus endpoint-ul WebSocket pentru detectia in timp real a ingredientelor din cadre video. Include clasa DetectionSmoother pentru stabilizarea temporala a detectiilor."
$descs["backend\requirements.txt"] = "Lista dependentelor Python necesare pentru backend: FastAPI, OpenCV, Ultralytics YOLO, NumPy, WebSockets."
$descs["backend\logic\__init__.py"] = "Fisier de initializare al modulului logic - exporta clasele RecipeMatcher si NutritionCalculator."
$descs["backend\logic\nutrition.py"] = "Calculator de nutritie - estimeaza valorile nutritionale (calorii, proteine, carbohidrati, grasimi, fibre) pentru ingredientele detectate, folosind date per portie din nutrition_data.json."
$descs["backend\logic\recipe_matcher.py"] = "Algoritm propriu de recomandare retete bazat pe Similaritatea Jaccard. Calculeaza un scor combinat din: similaritate Jaccard 40 procente, acoperire ponderata primary/secondary 35 procente si scor de complexitate 25 procente."
$descs["backend\vision\__init__.py"] = "Fisier de initializare al modulului vision - exporta clasele YOLODetector si CustomClassifier."
$descs["backend\vision\yolo_detector.py"] = "Detectorul YOLO - incarca modelul YOLOv8 custom antrenat si mapeaza clasele detectate la cele 9 ingrediente ale aplicatiei. Gestioneaza si candidatii ambigui pentru validarea ulterioara."
$descs["backend\vision\custom_classifier.py"] = "Clasificatorul matematic propriu (fara biblioteci ML) - valideaza detectiile YOLO folosind: segmentare HSV cu normalizare adaptiva a iluminarii CLAHE, texturi LBP implementate manual cu NumPy, histograme de culoare cu distanta chi-squared, analiza formei, densitatea muchiilor Sobel si discriminator de saturatie. Include si rejector de fundal."
$descs["backend\vision\reference_profiles.json"] = "Profile de referinta pentru fiecare ingredient - contin intervalele HSV, histogramele LBP si de culoare, intervalele de saturatie asteptate si raportul de aspect, folosite de clasificatorul matematic."
$descs["backend\data\nutrition_data.json"] = "Baza de date nutritionala - contine informatii per 100g pentru fiecare ingredient: calorii, proteine, carbohidrati, grasimi, fibre, portia standard si emoji."
$descs["backend\data\recipes.json"] = "Baza de date cu retete - 13 retete cu ingrediente primary/secondary, pasi de preparare, timp, dificultate, taguri, imagini si linkuri video YouTube."
$descs["backend\Dockerfile"] = "Dockerfile pentru backend - construieste imaginea Docker cu Python 3.11, instaleaza dependentele OpenCV si ruleaza serverul cu Uvicorn."
$descs["frontend\index.html"] = "Pagina HTML principala - punctul de intrare al aplicatiei React SPA, include meta taguri SEO si link catre manifest.json pentru PWA."
$descs["frontend\package.json"] = "Configurarea proiectului frontend - dependente React 19, dev dependencies Vite 8 si ESLint, si scripturi npm."
$descs["frontend\vite.config.js"] = "Configurarea Vite - plugin React si proxy pentru rutarea cererilor /api si /ws catre backend-ul FastAPI pe portul 8000."
$descs["frontend\eslint.config.js"] = "Configurarea ESLint - reguli pentru React hooks si React Refresh."
$descs["frontend\src\main.jsx"] = "Punctul de intrare React - randeaza componenta App in DOM cu StrictMode."
$descs["frontend\src\App.jsx"] = "Componenta principala App - orchestreaza camera, WebSocket-ul, starea ingredientelor acumulate persistent, cautarea retetelor si nutritiei via API, si afisarea interfetei complete."
$descs["frontend\src\index.css"] = "Sistemul de design CSS - tema dark premium cu glassmorphism, gradiente vibrante, variabile CSS custom, stiluri pentru toate componentele, animatii, scrollbar custom si design responsive."
$descs["frontend\src\components\Header.jsx"] = "Componenta Header - afiseaza logo-ul Smart Chef si badge-ul de status Live/Offline al conexiunii WebSocket."
$descs["frontend\src\components\IngredientChips.jsx"] = "Componenta IngredientChips - afiseaza ingredientele detectate ca chip-uri cu emoji si buton de stergere. Include un input cu autocomplete dropdown pentru adaugarea manuala a ingredientelor din lista predefinita."
$descs["frontend\src\components\ParticleBackground.jsx"] = "Componenta ParticleBackground - animeaza un fundal cu particule flotante cyan si violet conectate prin linii, folosind Canvas 2D."
$descs["frontend\src\components\RecipeCard.jsx"] = "Componenta RecipeCard - card de reteta cu imagine, badge procent potrivire, metadate timp si dificultate, bara de progres si taguri."
$descs["frontend\src\components\RecipeModal.jsx"] = "Componenta RecipeModal - modal detaliat pentru reteta selectata cu imagine, ingrediente matched/missing, taburi Pasi de preparare si Nutritie cu bare vizuale, link video YouTube si buton de inchidere."
$descs["frontend\src\components\WebcamDetector.jsx"] = "Componenta WebcamDetector - afiseaza feed-ul video de la camera si deseneaza bounding boxes cu etichete pe un canvas overlay pentru ingredientele detectate in timp real."
$descs["frontend\src\hooks\useWebcam.js"] = "Hook custom useWebcam - gestioneaza accesul la camera start/stop, captura cadrelor video ca base64 JPEG si curatarea stream-ului la unmount."
$descs["frontend\src\hooks\useWebSocket.js"] = "Hook custom useWebSocket - gestioneaza conexiunea WebSocket cu auto-reconectare, parsarea mesajelor JSON si trimiterea cadrelor base64 catre backend."
$descs["frontend\Dockerfile"] = "Dockerfile multi-stage pentru frontend - Stage 1: build React cu Node 20, Stage 2: servire statica cu Nginx Alpine."
$descs["frontend\nginx.conf"] = "Configurarea Nginx - compresie gzip, cache pentru assets statice, proxy pentru /api si /ws catre backend, si fallback SPA pentru rutare client-side."
$descs["frontend\public\manifest.json"] = "Manifestul PWA - defineste numele aplicatiei, culori tema, iconita si modul de afisare standalone."
$descs["docker-compose.yml"] = "Docker Compose - orchestreaza serviciile smartchef-backend pe portul 8000 si smartchef-frontend pe portul 80 cu health check si restart automat."

$files = @(
    "backend\app.py",
    "backend\requirements.txt",
    "backend\logic\__init__.py",
    "backend\logic\nutrition.py",
    "backend\logic\recipe_matcher.py",
    "backend\vision\__init__.py",
    "backend\vision\yolo_detector.py",
    "backend\vision\custom_classifier.py",
    "backend\vision\reference_profiles.json",
    "backend\data\nutrition_data.json",
    "backend\data\recipes.json",
    "backend\Dockerfile",
    "frontend\index.html",
    "frontend\package.json",
    "frontend\vite.config.js",
    "frontend\eslint.config.js",
    "frontend\src\main.jsx",
    "frontend\src\App.jsx",
    "frontend\src\index.css",
    "frontend\src\components\Header.jsx",
    "frontend\src\components\IngredientChips.jsx",
    "frontend\src\components\ParticleBackground.jsx",
    "frontend\src\components\RecipeCard.jsx",
    "frontend\src\components\RecipeModal.jsx",
    "frontend\src\components\WebcamDetector.jsx",
    "frontend\src\hooks\useWebcam.js",
    "frontend\src\hooks\useWebSocket.js",
    "frontend\Dockerfile",
    "frontend\nginx.conf",
    "frontend\public\manifest.json",
    "docker-compose.yml"
)

$result = New-Object System.Text.StringBuilder
$first = $true

foreach ($relPath in $files) {
    $fullPath = Join-Path "d:\SmartChef" $relPath
    if (-not (Test-Path $fullPath)) { continue }

    if (-not $first) {
        [void]$result.AppendLine($separator)
    }
    $first = $false

    [void]$result.AppendLine($relPath)
    if ($descs.ContainsKey($relPath)) {
        [void]$result.AppendLine($descs[$relPath])
    }
    [void]$result.AppendLine("")

    $lines = Get-Content $fullPath -Encoding UTF8
    $ext = [System.IO.Path]::GetExtension($relPath).ToLower()

    if ($ext -in @(".py")) {
        $inDocstring = $false
        $docstringChar = ""
        foreach ($line in $lines) {
            $trimmed = $line.Trim()

            if ($inDocstring) {
                if ($trimmed.Contains($docstringChar)) {
                    $inDocstring = $false
                }
                continue
            }

            if ($trimmed.StartsWith('"""') -or $trimmed.StartsWith("'''")) {
                $docstringChar = $trimmed.Substring(0,3)
                if ($trimmed.Length -gt 3 -and $trimmed.Substring(3).Contains($docstringChar)) {
                    continue
                }
                $inDocstring = $true
                continue
            }

            if ($trimmed.StartsWith("#")) {
                continue
            }

            if ($line.Contains(" #")) {
                $inStr = $false
                $strChar = ""
                $cutIdx = -1
                for ($i = 0; $i -lt $line.Length; $i++) {
                    $c = $line[$i]
                    if ($inStr) {
                        if ($c -eq $strChar) { $inStr = $false }
                    } else {
                        if ($c -eq '"' -or $c -eq "'") { $inStr = $true; $strChar = $c }
                        elseif ($c -eq '#') { $cutIdx = $i; break }
                    }
                }
                if ($cutIdx -gt 0) {
                    $line = $line.Substring(0, $cutIdx).TrimEnd()
                }
            }

            if ($trimmed -eq "") { [void]$result.AppendLine(""); continue }
            [void]$result.AppendLine($line)
        }
    }
    elseif ($ext -in @(".js", ".jsx")) {
        $content = $lines -join "`n"
        $content = [regex]::Replace($content, '/\*[\s\S]*?\*/', '')
        $content = [regex]::Replace($content, '\{/\*[\s\S]*?\*/\}', '')
        $outLines = $content -split "`n"
        foreach ($line in $outLines) {
            $trimmed = $line.Trim()
            if ($trimmed.StartsWith("//")) { continue }
            if ($trimmed -eq "") { [void]$result.AppendLine(""); continue }
            if ($line.Contains(" //")) {
                $inStr = $false
                $strChar = ""
                $cutIdx = -1
                for ($i = 0; $i -lt $line.Length - 1; $i++) {
                    $c = $line[$i]
                    if ($inStr) {
                        if ($c -eq $strChar) { $inStr = $false }
                    } else {
                        if ($c -eq '"' -or $c -eq "'" -or $c -eq '`') { $inStr = $true; $strChar = $c }
                        elseif ($c -eq '/' -and $line[$i+1] -eq '/') { $cutIdx = $i; break }
                    }
                }
                if ($cutIdx -gt 0) {
                    $line = $line.Substring(0, $cutIdx).TrimEnd()
                }
            }
            [void]$result.AppendLine($line)
        }
    }
    elseif ($ext -eq ".css") {
        $content = $lines -join "`n"
        $content = [regex]::Replace($content, '/\*[\s\S]*?\*/', '')
        $outLines = $content -split "`n"
        foreach ($line in $outLines) {
            $trimmed = $line.Trim()
            if ($trimmed -eq "") { [void]$result.AppendLine(""); continue }
            [void]$result.AppendLine($line)
        }
    }
    elseif ($ext -eq ".html") {
        $content = $lines -join "`n"
        $content = [regex]::Replace($content, '<!--[\s\S]*?-->', '')
        $outLines = $content -split "`n"
        foreach ($line in $outLines) {
            $trimmed = $line.Trim()
            if ($trimmed -eq "") { [void]$result.AppendLine(""); continue }
            [void]$result.AppendLine($line)
        }
    }
    elseif ($relPath -like "*Dockerfile*" -or $ext -eq ".yml" -or $ext -eq ".conf") {
        foreach ($line in $lines) {
            $trimmed = $line.Trim()
            if ($trimmed.StartsWith("#")) { continue }
            if ($trimmed -eq "") { [void]$result.AppendLine(""); continue }
            [void]$result.AppendLine($line)
        }
    }
    else {
        foreach ($line in $lines) {
            [void]$result.AppendLine($line)
        }
    }

    [void]$result.AppendLine("")
}

[System.IO.File]::WriteAllText($output, $result.ToString(), [System.Text.Encoding]::UTF8)
Write-Host "DONE - wrote $output"
