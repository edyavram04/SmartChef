# Documentație Proiect: Smart Chef - Sistem Inteligent de Recunoaștere a Ingredientelor și Recomandare de Rețete

**Autor:** [Numele tău], [Grupa ta]
**Anul:** 2

---

## 1. Introducere și Obiectivele Proiectului

În era digitalizării accelerate, eficientizarea timpului și reducerea risipei alimentare reprezintă provocări cotidiene pentru majoritatea persoanelor. Proiectul **Smart Chef** a fost dezvoltat pornind de la necesitatea de a oferi utilizatorilor o modalitate rapidă, interactivă și intuitivă de a descoperi rețete culinare pe baza ingredientelor pe care le au deja la dispoziție, utilizând direct camera web.

**Relevanța temei:** Abordarea manuală a căutării de rețete (introducerea textului într-un motor de căutare) este adesea greoaie când utilizatorul se află în bucătărie. Prin integrarea tehnologiilor de *Computer Vision*, Smart Chef transformă procesul de gătit într-o experiență fluidă. Sistemul nu este doar o aplicație teoretică, ci propune o rezolvare aplicată pentru diminuarea risipei alimentare (folosind ce ai în frigider) și optimizarea timpului.

**Obiectivele principale:**
1. Realizarea unui sistem capabil să detecteze vizual ingrediente în timp real, direct din browser, fără instalări adiționale.
2. Implementarea unei arhitecturi software hibride care să combine modele pre-antrenate de Inteligență Artificială (YOLO) cu algoritmi matematici de validare customizați (prin OpenCV).
3. Dezvoltarea unei interfețe web cu un design premium (Dark Mode, Glassmorphism), oferind un mediu multimedia bogat (recomandări, imagini și conținut video).
4. Evitarea "efectului de black-box" al AI-ului, demonstrând controlul absolut asupra prelucrării imaginilor la nivel matricial.

Fată de proiectele existente care se bazează adesea doar pe introducerea de text, **Smart Chef** inovează prin fluxul său continuu de prelucrare video asincronă, fiind proiectat să asigure o experiență stabilă și performantă chiar și pe dispozitive client cu o putere de calcul limitată.

---

## 2. Suportul Tehnic și Stadiul Actual al Domeniului

Domeniul aplicațiilor culinare este unul vast, însă majoritatea soluțiilor comerciale depind de inputul manual al utilizatorului. O analiză a pieței arată câteva realizări similare:
* **SuperCook** și **MyFridgeFood**: Sunt platforme web extrem de populare [1]. Punctul lor forte este baza imensă de rețete, însă punctul slab constă în modalitatea rudimentară de interacțiune: utilizatorul trebuie să selecteze manual zeci de căsuțe (checkbox-uri) pentru a adăuga ingredientele.
* **Samsung Food (fostul Whisk)**: O soluție complexă cu un AI puternic pentru generarea de liste de cumpărături [2]. Deși oferă o experiență premium, detecția automată lipsește din interfața nativă web, necesitând instalarea unei aplicații mobile dedicate.

Raportându-ne la acestea, **Smart Chef** aduce un avantaj major: aduce puterea procesării de imagini direct pe o pagină web, fără interacțiune fizică constantă (touch/click).

### Aspecte Teoretice Fundamentale (Multimedia și Computer Vision)
Pentru atingerea obiectivelor, aplicația operează cu concepte fundamentale de multimedia și procesare de semnal:
* **Reprezentarea Imaginii:** În memoria calculatorului, o imagine nu este altceva decât o structură de date de tip matrice multi-dimensională. O imagine color standard este o matrice 3D (Lățime x Înălțime x 3 Canale de culoare - Red, Green, Blue). Orice manipulare a imaginii reprezintă, în esență, aplicarea unor operații algebrice (adunări, înmulțiri) asupra acestor numere cuprinse între 0 și 255 [3].
* **Protocoale de Comunicare în Timp Real:** HTTP-ul clasic este unidirecțional (Request-Response). Pentru a asigura transmiterea continuă a cadrelor video fără blocaje, proiectul se bazează pe **WebSockets** [4]. Acesta este un protocol TCP full-duplex care menține un „tunel” permanent deschis între browser și server.
* **Compresia Video/Imagine:** Cadrele preluate de camera web sunt transformate într-un flux Base64 (un algoritm de codificare care transformă datele binare în text ASCII). Aceasta reprezintă o formă de împachetare a datelor JPEG pentru a tranzita eficient canalul de rețea.

---

## 3. Prezentarea Tehnică a Etapei de Implementare

În concordanță cu exigențele unei arhitecturi software moderne, sistemul a fost proiectat pe principiul separării responsabilităților (*Separation of Concerns*). Partea tehnică a lucrării detaliază nucleul logic al aplicației, demonstrând interconectarea dintre nivelul de prezentare, transferul datelor de streaming și validarea pur matematică a imaginilor.

### 3.1. Arhitectura Generală și Instrumentele Utilitare

Proiectul a fost divizat în două medii de execuție independente, asigurând astfel scalabilitatea și independența modulelor:

1. **Nivelul de Prezentare (Frontend - React.js și Vite):** 
Interfața este construită ca un *Single Page Application (SPA)*. S-a ales React pentru abilitatea sa de a gestiona stări locale asincrone (*Hooks*) și pentru utilizarea *Virtual DOM*-ului. Acest mecanism evită reîncărcarea greoaie a paginilor, redesenând în browser doar acele porțiuni de ecran (cum ar fi noile etichete de ingrediente) a căror stare de memorie s-a modificat. Vite a fost selectat ca instrument de asamblare datorită timpului de compilare extrem de redus și a funcției de *Hot Module Replacement*.

2. **Nivelul de Logică și Procesare (Backend - Python 3.11 și FastAPI):**
Deoarece procesarea vizuală implică un calcul matematic intensiv pe array-uri (matricelor de pixeli), limbajul Python, prin extensia NumPy scrisă în C, a fost singura alegere fezabilă. FastAPI reprezintă scheletul serverului web. Spre deosebire de framework-urile mai vechi (precum Flask sau Django), FastAPI operează asincron via o buclă de evenimente (*event-loop* standardizat ASGI), ceea ce înseamnă că sistemul poate primi cadre video de la mai multe camere simultan fără a bloca firul de execuție principal.

### 3.2. Fluxul de Execuție și Arhitectura Multimedia

Inima acestui proiect o reprezintă modalitatea de transfer și procesare a elementelor multimedia în timp real. HTTP-ul clasic, de tip „cerere-răspuns”, creează latențe ridicate. Prin urmare, s-a implementat o arhitectură orientată pe evenimente continue.

* **Captarea și eșantionarea (Sampling):** Folosind *MediaDevices API* din browserul nativ, semnalul web camerei este proiectat invizibil într-un element HTML de tip `<canvas>`. Un temporizator (interval asincron) captează o „fotografie” a acestui canvas exact la fiecare 600 de milisecunde.
* **Codificarea la sursă:** Matricea de pixeli este transformată dintr-un format brut (Bitmap) într-un șir de caractere *Base64*. Acest proces este o codificare de nivel superior ce transformă datele binare JPEG în caractere ASCII sigure, evitând coruperea datelor pe canalul de rețea.
* **Tunelul de comunicație (WebSockets):** Cadrele Base64 sunt lansate printr-o magistrală *WebSocket* (conform RFC 6455). Conexiunea, odată stabilită, rămâne deschisă permanent. Viteza de transfer devine astfel dependentă strict de banda de rețea, eliminând timpul irosit pentru stabilirea conexiunilor noi (TCP Handshake).
* **Decodificarea pe server:** Ajuns în Backend, șirul Base64 este convertit înapoi în octeți binari (`bytes`) și reconstituit imediat de biblioteca OpenCV într-o structură matematică tridimensională (Lățime x Înălțime x Canale de culoare RGB).

### 3.3. Antrenarea Modelului AI și Algoritmul Hibrid de Detecție

Pentru a obține o recunoaștere vizuală precisă, o contribuție majoră a acestui proiect o constituie **antrenarea personalizată a modelului de Inteligență Artificială**. Utilizarea unui model generic pre-antrenat (cum sunt cele de pe setul de date COCO) prezintă un dezavantaj major: astfel de modele sunt concepute să recunoască mașini, animale sau obiecte casnice generale. Dacă li se expune un aliment, fie nu îl detectează deloc, fie emit rezultate complet eronate (de exemplu, pot confunda un castravete cu un obiect cilindric oarecare).

Pentru a remedia acest aspect, am antrenat (printr-un proces de *fine-tuning*) o rețea neurală din clasa **YOLOv8s** pe un set vast și atent curatoriat de imagini conținând legume, fructe și ingrediente. Astfel, modelul personalizat a învățat să recunoască siluetele specifice ale alimentelor în diverse unghiuri. În aplicație, acest model joacă rolul de „cercetaș vizual”: el scanează rapid întregul cadru, ignoră „zgomotul” (cum ar fi masa, farfuria sau mâinile utilizatorului) și izolează alimentul, trasând deasupra acestuia o casetă de identificare spațială (*Bounding-Box*).

**De ce mai este necesară validarea matematică dacă AI-ul a fost antrenat pe legume?**
Modelele de rețele neurale se bazează pe inferențe probabilistice (ghicit statistic). Dacă lumina din cameră este slabă sau dacă expunem o roșie verde și un măr verde, AI-ul antrenat le poate încurca, ambele fiind forme rotunde și verzi. Din acest motiv, a doua inovație arhitecturală (și o decizie esențială de design a proiectului) a fost crearea unui **sistem hibrid**, limitând AI-ul strict la stadiul de *proposer* de regiuni (Region of Interest - ROI). 

AI-ul identifică rapid conturul brut și emite o ipoteză (ex. „Sunt 80% sigur că aici este o roșie”), însă nu are voie să adauge ingredientul direct în aplicație. Coordonatele acelei casete (*Bounding-Box*) sunt preluate, porțiunea de imagine este decupată și trimisă mai departe către propriii mei algoritmi dezvoltați în Python. Aici, OpenCV acționează ca un filtru matematic absolut: el verifică „la sânge” pixelii din interiorul casetei la nivel de textură și de spectru de culoare. Dacă matematica confirmă că rugozitatea corespunde unei roșii, abia atunci detecția devine validă. Astfel, decizia finală aparține matematicii deterministe și nu poate fi păcălită de iluziile optice sau de condițiile slabe de iluminare, transformând aplicația într-una extrem de fiabilă.

### 3.4. Aparatul Matematic din Spatele Validării (Efecte și Procesare)

În procesarea video în timp real, scrierea de la zero a algoritmilor de manipulare matricială în Python pur ar introduce întârzieri majore. Astfel, pentru execuția propriu-zisă, am integrat funcțiile optimizate (scrise în C/C++) ale bibliotecii OpenCV. Cu toate acestea, contribuția mea arhitecturală nu s-a rezumat la un simplu „apel de funcții”, ci a presupus o parametrizare și o orchestrare riguroasă a acestora. Mai jos prezint aparatul matematic fundamental [5] pe care se bazează funcțiile apelate, demonstrând raționamentul pentru care le-am ales:

**A. Maparea în Spațiul Cilindric HSV și Pragul Binar (Hard Thresholding)**
O cameră standard furnizează o matrice de culori RGB. Problema majoră a acestui format liniar este dependența cromatică de lumină: o lampă cu lumină caldă adaugă valori matematice pe toate cele trei axe (R, G, B), denaturând obiectul. 
Pentru rezolvarea acestei instabilități, sistemul transformă datele matriceale non-liniar în modelul **HSV** (*Hue, Saturation, Value*). Prin acest procedeu, extragem și ignorăm complet axa de luminozitate (*Value*), axându-ne exclusiv pe *Hue* (Nuanța pură, exprimată pe un cerc trigonometric).
Pentru a extrage obiectul din fundal, se aplică operații logice la nivel de biți (*Bitwise AND*). Când parcurgem matricea, se compară fiecare pixel cu banda cromatică a ingredientului: dacă se află în spectrul vizat, pixelului i se atribuie valoarea 1. Restul elementelor din matrice devin 0. Așa generăm o **mască binară** care reține doar aria fizică a alimentului, curățată de umbre.

**B. Convoluția Matricială: Efectul de Netezire (Blur)**
Deoarece orice mască brută conține „zgomot” de senzor (pixeli paraziți), aplicăm un aparat matematic de filtrare liniară cunoscut sub numele de efect de *Blur* (Netezire).
Acest efect reprezintă, din punct de vedere academic, o operație de **convoluție**. Presupune trecerea unei matrice reduse, denumită *kernel* (în cazul de față, o arie de dimensiune 5x5 pixeli), treptat deasupra întregii imagini. Pentru fiecare poziție, noul pixel central nu mai poartă valoarea originală, ci devine matematic media aritmetică a tuturor pixelilor vecini acoperiți de kernel. Această ecuație simplă garantează eliminarea aspră a aberațiilor fine de imagine, marginile ingredientului devenind mult mai clare.

**C. Analiza Matematică a Texturii: Local Binary Patterns (LBP)**
Culoarea nu este un indicator suficient; un măr roșu nu trebuie confundat cu o roșie. Pentru diferențiere, se recurge la extragerea texturii.
Algoritmul implementat (LBP) scanează zona ingredientului evaluând sub-matrice logice de dimensiune 3x3. Pixelul central al acestei vecinătăți acționează drept prag de filtrare: dacă un vecin periferic are o intensitate luminoasă mai mare sau egală, i se atribuie cifra 1. Altfel primește 0. Citind toți cei 8 vecini din jurul centrului, generăm un număr binar cu lungimea de 8 biți, ce constituie o amprentă spațială a nivelului de „rugozitate”. Adunând toate aceste tipare locale se compune o histogramă de frecvență a texturii. Prin compararea acestei histograme curente cu cea etalon a ingredientului vizat, ecuația respinge obiectul dacă textura este greșită, desăvârșind decizia sistemului.

### 3.5. Logica de Recomandare și Teoria Mulțimilor (Jaccard Index)

Odată ce lista de ingrediente validate vizual se acumulează în starea frontend-ului, trebuie efectuată interogarea bazei de date. În locul unei simple căutări secvențiale (iterarea simplă prin listă), modulul de logică de business modelează sistemul folosind *Teoria Mulțimilor*.
Fie $A$ mulțimea ingredientelor de pe masa utilizatorului, și $B$ mulțimea ingredientelor necesare pentru o rețetă din dicționarul sistemului.
Aplicația evaluează potrivirea perfectă prin calcularea Indexului de Similitudine Jaccard:
$$ J(A,B) = \frac{| A \cap B |}{| A \cup B |} $$
Aplicația execută operațiile de intersecție (câte ingrediente avem în comun) și reuniune, ordonând răspunsul către client într-un clasament descrescător. Astfel, algoritmul recomandă mai întâi acele preparate care maximizează utilitatea ingredientelor existente, îndeplinind obiectivul de reducere a risipei alimentare. Răspunsul este transformat într-un obiect de transport date (JSON) și expediat înapoi prin tunelul WebSocket.

---

## 4. Mod de Utilizare și Interacțiune cu Utilizatorul

Interacțiunea cu aplicația a fost gândită să fie complet non-invazivă. 
*(Aici se vor introduce în documentul Word 2-3 imagini echilibrate. Acestea nu trebuie să depășească 20% din volumul lucrării)*

**1. Pornirea Sistemului:** 
Fiind un mediu izolat în Docker, utilizatorul nu are nevoie de instalări complexe, ci doar de comanda de inițializare a containerelor. Alternativ, dezvoltatorul folosește comenzi standard de mediu virtual Python și `npm run dev` pentru serverul de interfață web.

**2. Pagina Principală și Detectarea**
`[Aici se va insera CAPTURĂ DE ECRAN 1: Interfața principală cu camera oprită]`
Odată deschisă aplicația (pe `localhost:5173`), utilizatorul apasă butonul „Start Camera”. Conexiunea WebSocket este stabilita în fundal, fiind confirmată vizual de indicatorul luminos din header ("Connected").

**3. Adăugarea Ingredientelor și Generarea Rețetelor**
Dacă utilizatorul plasează un obiect valid în fața camerei (ex: Banana, Ou, Tomată), sistemul va genera un vizual de tip Bounding-Box exact peste obiect pe ecranul video, iar elementul va fi adăugat automat în „Coșul de Ingrediente” (secțiunea Detected Ingredients) sub formă de chip (etichetă vizuală).
Pentru scenariile în care un ingredient e prea mare sau e ținut în congelator, aplicația oferă și o casetă de text de tip Dropdown cu validare automată (Autocomplete) de unde se pot adăuga sau elimina elemente manual.

`[Aici se va insera CAPTURĂ DE ECRAN 2: Fereastra aplicației identificând un obiect și afișând lista de rețete compatibile dedesubt]`

Imediat ce lista are cel puțin un ingredient, secțiunea de „Rețete Recomandate” afișează dinamic cardurile rețetelor ordonate după compatibilitatea matematică Jaccard calculată anterior. O rețetă completată va deschide un modal multimedia ce afișează pașii de execuție, macronutrienții calculați (Carbohidrați, Proteine, Calorii) și un player video pentru rețeta efectivă.

---

## 5. Testarea Soluției și Demonstrarea Performanței

Pentru a demonstra stabilitatea aplicației și pentru a evita funcționarea doar în scenarii „ideale”, sistemul a fost testat pe un set de **Situații Limită (Edge-cases)**:

1. **Testul de Iluminare Dificilă (Bucătărie noaptea):** 
Am expus camera la iluminare incandescentă puternică, care îngălbenește considerabil imaginea. Datorită convertirii matematice în mediul cilindric HSV, algoritmii noștri au izolat componenta de luminozitate (Value) și au evaluat puritatea pixelului (Hue). Detecția a funcționat impecabil, sistemul recunoscând un "Ou" chiar dacă pe ecran părea de culoare portocalie, demonstrând că logica custom depășește un senzor optic simplu.

2. **Testul de "Flickering" (Inerția Temporală):**
Un defect comun la aplicațiile de Computer Vision este „clipitul” interfeței — când un algoritm nu este sigur și obiectul este recunoscut de zeci de ori pe secundă activând/dezactivând stări pe ecran. Am rezolvat și testat această vulnerabilitate aplicând principiul *Temporal Smoothing*. Codul din Backend menține un buffer al ultimelor 5 cadre evaluate și returnează un rezultat doar dacă ingredientul are o medie matematică de prezență de cel puțin 3 din 5, menținând interfața calmă și constantă pentru utilizator.

**Performanță:** Din punctul de vedere al latenței, deși facem operațiuni matematice masive (procesarea a sute de mii de pixeli per cadru), asincronicitatea oferită de FastAPI și tunelul continuu de WebSockets duc la o latență de afișare mai mică de 50ms per operațiune. Acest lucru garantează faptul că utilizatorul nici nu simte că imaginile sunt trimise și procesate la distanță, oferind o performanță net superioară alternativelor statice.

---

## 6. Concluzii

Proiectul **Smart Chef** reușește să își îndeplinească obiectivele propuse la momentul inițierii. Nu doar că oferă o aplicație complet operațională de asistență în bucătărie prin Computer Vision, dar rezolvă într-un mod elegant problema comunicării latente între mediul web și procesarea de imagine.

**Impact și Actualitate:** Într-o eră dominată de Soluții "Black-Box" de tip AI oferite prin API-uri terțe, Smart Chef propune o metodologie prin care Inteligența Artificială (YOLO) colaborează intim cu instrumentele matematice tradiționale de extracție a texturii (LBP) și filtrare coloristică (HSV), aducând decizia finală înapoi sub controlul matematic al programatorului.

**Avantaje Competitoriale:** Prin interfața web "zero-install", care acționează similar unei aplicații native de telefon via Vite și React, eliminăm complet barierele de intrare pentru utilizator. Experiența non-verbală și interactivă recomandă platforma drept un asistent util și practic, depășind abordările rudimentare manuale existente momentan pe piața web gratuită. Abordarea hibridă folosită va permite pe viitor scalarea ușoară prin adăugarea de sute de clase de alimente.

---

## 7. Referințe Bibliografice

1. SuperCook (Accesat Martie 2026), "Zero Waste Recipe Generator", Documentație Web. https://www.supercook.com
2. Samsung Electronics (Accesat Martie 2026), "Samsung Food / Whisk platform", Prezentare Platformă. https://samsungfood.com
3. Bradski, G., Kaehler, A. (2008). *Learning OpenCV: Computer Vision with the OpenCV Library*. O'Reilly Media, ISBN: 978-0596516130, pp. 25-45.
4. Fette, I., Melnikov, A. (2011). *The WebSocket Protocol (RFC 6455)*. Internet Engineering Task Force (IETF). Documentație Internet. https://tools.ietf.org/html/rfc6455
5. Szeliski, R. (2010). *Computer Vision: Algorithms and Applications*. Springer, ISBN: 978-1848829343, Capitolul 3: "Image Processing" (Filtrarea Liniară și Spații de Culoare).
6. Jocher, G., Chaurasia, A., Qiu, J. (2023). *Ultralytics YOLOv8 Architecture and Capabilities*. Ultralytics. https://github.com/ultralytics/ultralytics
