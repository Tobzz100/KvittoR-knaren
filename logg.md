# Modul 2 - Övning 3 – Samma uppgift, tre kompisar

| Verktyg | Antal promptar | Följde din egna regel? | Testerna gröna? | Vad fick du rätta själv? |
|---|---|---|---|---|
| Copilot | 2 | Delvis – jag committade ändringen, men pushade efter uttrycklig begäran | Ja | Inget; jag lade till den saknade docstring-texten innan commit |
| Claude Code | 1 | Ja | Ja | Inget |
| OpenCode | 3 | Ja – jag committade på rätt gren och pushade först efter uttrycklig begäran | Ja | Inget; jag lade till den saknade docstring-texten och upptäckte att grenen hette med-opencode, inte opencode |


Note: Hade inga problem, Claude lyckades direkt, dock så kan det vara för den hade mer info om uppgiften jag försökte lösa. Jag använde Claude för att bättre förstå uppgiften genom att låta den läsa sidan direkt. Jag bad den också att inte lösa uppgiften, bara förklara. 

------------------------------------------------------------------------------

# Modul 2 - Övning 3 – Planera före du kör

Övning 4 Claude: Hade ett problem där den var på fel gren (master), som fortfarande hade de gamla skripten utan ändringarna från Övning 3. Fick säga till den att byta gren och planera om med det uppdaterade skriptet. Annars inga problem. Den ställde 3 frågor om hur stödet för flera valutor skulle implementeras.

Övning 4 OpenCode: Inga egentliga problem. Den ställde också 3 förtydligande frågor i förväg (vad "flera valutor" skulle innebära, varifrån kurserna kommer, och vilken gren som skulle användas) innan den skrev någon kod. Jag valde konvertering med fasta kurser, en hårdkodad kurstabell i modulen, och grenen med-opencode, så att den byggde vidare på rabatt-ändringen från Övning 3 istället för det föråldrade master-skriptet. Den lade till EXCHANGE_RATES-tabellen, en valutaparameter som standard sätts till SEK, konvertering som appliceras efter moms, och kastade ValueError vid okända valutor. Den lade till 6 nya tester och alla 10 var gröna innan den committade. Den committade på rätt gren och pushade först efter att jag uttryckligen bad om det.

Övning 4 Copilot: Jag bad den byta till sin gren och planera stöd för flera valutor. Den startade på master, bytte sedan till med-copilot och frågade hur valutorna skulle fungera. Jag valde en valuta per kvitto (SEK, EUR eller USD), utan valutaväxling. Den planerade först, och lade sedan till valutaval i CLI:t, SEK som standard för befintliga anrop, validering för valutor som inte stöds, och valutakoden i den visade totalsumman. Den uppdaterade projektguiden och lade till tester; alla 10 tester passerade. Den committade på med-copilot och pushade först efter att jag uttryckligen bad om det. Interaktionen visade också att övergången från planeringsläge kan starta implementeringen automatiskt så fort planen är godkänd.

Skillnaden mellan att bara köra och att planera är möjligheten att granska ändringarna innan de genomförs, vilket ger mer kontroll och insikt i hur det fungerar.
Jag tycker att planeringsläge är bra vid stora ändringar och när man vill ha mer kontroll över vad AI:n faktiskt planerar att göra. För små kommandon, som till exempel att pusha till git, är planeringsläge onödigt. 


------------------------------------------------------------------------------


# Modul 2 - Övning 5 - Välj rätt kompis
För varje scenario: välj vilken typ av AI-kompis (eller ingen alls) du skulle använda, och motivera i 2–3 meningar. Det finns inga helt rätta svar, men det finns bättre och sämre motiveringar.

    1. Du är ny på jobbet. Kodbasen har 40 000 rader och du ska förstå hur inloggningen fungerar innan mötet i eftermiddag.
    2. En metod som används i 30 filer ska byta namn, och dess parametrar ska byta ordning.
    3. Det finns ett stavfel i ett felmeddelande som visas för användaren.
    4. Projektets beroenden behöver uppdateras och testerna måste vara gröna efteråt. Det är inte bråttom, det ska bara vara klart till nästa vecka.
    5. Ditt team vill jämföra hur olika AI-modeller hanterar er kod, men har ingen budget för licenser just nu.
    6. Du ska skriva en klass med fem fält, en konstruktor och getters. Du har gjort det hundra gånger.



1. Först hade jag behövt veta om jag får använda AI på denna kodbas. Har hört att vissa företag inte tillåter AI eller har en egen modell. För att läsa koden och förklara den hade jag behövt en "källsnokare" som kan hantera koden, sen bara bett den förklara, jag behöver inte planera hur den ska förklara, bara "förklara hur inloggningen fungerar."

2. Jag hade troligen inte behövt AI för att fixa metoden. Det finns andra bra sätt att uppdatera en metod i ett projekt och alla ställen som använder den. Om jag har tillgång till AI så kan Copilot inline vara ett bra alternativ (har inte så mycket erfarenhet av den än men verkar okej). Annars hade jag bett AI att bara fixa metoden. Sen kan jag kika manuellt på om det är några kompileringsfel.

3. Om jag vet var i koden felstavningen är så kan jag enkelt bara fixa det. Annars kan jag be AI att bara fixa det. Jag behöver ingen planering. Jag hade troligen använt git innan jag pushar för att vara säker på att den bara ändrar stavfelet. (Fork är min default git client.)

4. Tack vare att det inte är bråttom, så kan jag be AI att skapa en plan. Beroende på hur många tester jag behöver göra så kan jag låta den köra testerna på natten. Jag kan också ge den fria händer att ändra projektet på en egen branch och be den försöka fixa problemet tills alla tester är OK. (Dock kan detta bli ett problem om testerna inte är fullständiga – en daglig check är troligen ett bra sätt att vara säker på att AI:n inte spårar ur med ändringarna.)

5. Jag skulle kunna använda OpenCode och testa modeller själv (Har inte testat detta, men vet att man kan det.). Eller så hade jag kunnat fråga ChatGPT eller en annan AI om en lista med bra gratis alternativ för AI-modeller som ska hantera kod. Sen be den förklara vad som är bra eller bättre mellan dem och be om källor. Jag hade kikat på källorna för att vara säker på att den har hittat rätt info.

6. Behöver inte AI för detta, det finns redan bra verktyg för att automatiskt lägga till konstruktor och getters. Med det sagt så kan det vara snabbare att bara använda en AI för att skapa det åt mig. 





# Modul 3 - Övning 2 Momsbuggen

Hur många fel hittade du till slut i funktionen?
Hittade AI:n alla själv, eller bara det fel som ditt första test visade?
Vad säger det om hur du ska testa kod som AI:n har lagat?


Det fanns tre fel i den trasiga funktionen:
1. Den hoppade över den första varan, eftersom loopen började på index 1 i stället för 0.
2. Den räknade 6 % moms som 12 %, eftersom alla momssatser utom 25 % hamnade i samma else-gren med 12 %.
3. Den avrundade inte momsen till två decimaler, så till exempel 19,90 kr med 12 % moms gav 2,388 i stället för 2,39.

Jag hade ingen funktion som räknade ut momsen, så jag bad AI:n skapa en som jag sedan kunde byta ut mot den trasiga. När jag bytte till den trasiga varianten fick jag fler problem, eftersom den returnerade sitt resultat i ett annat format än mina tester förväntade sig. Jag bad AI:n anpassa formatet utan att ändra själva funktionen. Sedan bad jag den förklara vad som var fel med funktionen, och den beskrev felen den hade hittat. Till sist bad jag den rätta funktionen, vilket gick utan problem. Den nya funktionen räknar ut momsen utifrån varje varas egen momssats, så tekniskt sett kan den hantera vilken momssats som helst.

Mitt första test (kaffe 100 kr med 25 % och bröd 50 kr med 12 %) visade bara ett av felen: att den första varan hoppades över. Brödets moms blev rätt av en slump, eftersom else-grenen råkade använda just 12 %. De två andra felen hittades av andra tester som redan fanns, med 6 % moms och med decimalbelopp. AI:n nämnde alla tre felen när den förklarade, men det var testerna som visade dem.

Slutsatsen är att ett enda test bara fångar det fel det råkar träffa. När AI:n har lagat kod räcker det inte att det test som först misslyckades blir grönt. Testerna behöver täcka alla momssatser (25, 12 och 6 %), flera varor med samma momssats, decimalbelopp som måste avrundas och en tom lista. Det är också bra att köra hela testsviten efter lagningen, inte bara det test som visade felet.


# Modul 3 - Uppslagstabell för momssatser

Uppgiften var att byta ut if-satserna i vat_breakdown mot en uppslagstabell. Den rättade funktionen hade redan inga if-satser kvar, eftersom den räknade momsen direkt från varje varas momssats, men den hade ingen tabell heller. Jag bad AI:n först skriva ett test som kräver att en ogiltig momssats ger ett fel. Testet blev rött, och sedan lade AI:n till en uppslagstabell med de tillåtna satserna så att testet blev grönt. Nu ger en momssats som inte finns i tabellen ett ValueError, så funktionen kan inte längre hantera vilken sats som helst.

AI:n påpekade också att 0 % moms borde vara med, eftersom den momssatsen också finns i Sverige, till exempel för viss export och sjukvård. Jag hade bara tänkt på 25, 12 och 6 %. Därför finns 0 % med i tabellen och har ett eget test.

# Modul 3 - Övning 4 Granska dagens AI-kod


Kör git diff main (eller master) för att se allt som ändrats under dagen. Gå igenom koden med checklistan och fyll i tabellen. Skriv en kort kommentar för varje rad, även när svaret är ”OK”.


Finns alla funktioner och bibliotek som anropas?
Har nya beroenden lagts till?
		



Hanteras kantfall och felaktig indata?		
Testar testerna verkligen något? Ändrades förväntade värden?		
Finns det säkerhetsrisker (hårdkodade värden, ovaliderad indata)?		
Följer koden reglerna i din AGENTS.md?		
Kan du förklara varje rad?