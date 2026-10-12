# Övning 3 – Logg

| Verktyg | Antal promptar | Följde din egna regel? | Testerna gröna? | Vad fick du rätta själv? |
|---|---|---|---|---|
| Copilot | 2 | Delvis – jag committade ändringen, men pushade efter uttrycklig begäran | Ja | Inget; jag lade till den saknade docstring-texten innan commit |
| Claude Code | 1 | Ja | Ja | Inget |
| OpenCode | 3 | Ja – jag committade på rätt gren och pushade först efter uttrycklig begäran | Ja | Inget; jag lade till den saknade docstring-texten och upptäckte att grenen hette med-opencode, inte opencode |


Note: Hade inga problem, Claude lyckades direkt, dock så kan det vara för den hade mer info om uppgiften jag försökte lösa. Jag använde Claude för att bättre förstå uppgiften genom att låta den läsa sidan direkt. Jag bad den också att inte lösa uppgiften, bara förklara. 

------------------------------------------------------------------------------

Övning 4

Övning 4 Claude: Hade ett problem där den var på fel gren (master), som fortfarande hade de gamla skripten utan ändringarna från Övning 3. Fick säga till den att byta gren och planera om med det uppdaterade skriptet. Annars inga problem. Den ställde 3 frågor om hur stödet för flera valutor skulle implementeras.

Övning 4 OpenCode: Inga egentliga problem. Den ställde också 3 förtydligande frågor i förväg (vad "flera valutor" skulle innebära, varifrån kurserna kommer, och vilken gren som skulle användas) innan den skrev någon kod. Jag valde konvertering med fasta kurser, en hårdkodad kurstabell i modulen, och grenen med-opencode, så att den byggde vidare på rabatt-ändringen från Övning 3 istället för det föråldrade master-skriptet. Den lade till EXCHANGE_RATES-tabellen, en valutaparameter som standard sätts till SEK, konvertering som appliceras efter moms, och kastade ValueError vid okända valutor. Den lade till 6 nya tester och alla 10 var gröna innan den committade. Den committade på rätt gren och pushade först efter att jag uttryckligen bad om det.

Övning 4 Copilot: Jag bad den byta till sin gren och planera stöd för flera valutor. Den startade på master, bytte sedan till med-copilot och frågade hur valutorna skulle fungera. Jag valde en valuta per kvitto (SEK, EUR eller USD), utan valutaväxling. Den planerade först, och lade sedan till valutaval i CLI:t, SEK som standard för befintliga anrop, validering för valutor som inte stöds, och valutakoden i den visade totalsumman. Den uppdaterade projektguiden och lade till tester; alla 10 tester passerade. Den committade på med-copilot och pushade först efter att jag uttryckligen bad om det. Interaktionen visade också att övergången från planeringsläge kan starta implementeringen automatiskt så fort planen är godkänd.

Skillnaden mellan att bara köra och att planera är möjligheten att granska ändringarna innan de genomförs, vilket ger mer kontroll och insikt i hur det fungerar.
Jag tycker att planeringsläge är bra vid stora ändringar och när man vill ha mer kontroll över vad AI:n faktiskt planerar att göra. För små kommandon, som till exempel att pusha till git, är planeringsläge onödigt. 


------------------------------------------------------------------------------