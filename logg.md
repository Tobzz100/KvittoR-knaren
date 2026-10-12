# Övning 3 – Logg

| Verktyg | Antal promptar | Följde din egna regel? | Testerna gröna? | Vad fick du rätta själv? |
|---|---|---|---|---|
| Copilot | 2 | Delvis – jag committade ändringen, men pushade efter uttrycklig begäran | Ja | Inget; jag lade till den saknade docstring-texten innan commit |
| Claude Code | 1 | Ja | Ja | Inget |
| OpenCode | 3 | Ja – jag committade på rätt gren och pushade först efter uttrycklig begäran | Ja | Inget; jag lade till den saknade docstring-texten och upptäckte att grenen hette med-opencode, inte opencode |


Note: Hade inga problem, Claude lyckades direkt, dock så kan det vara för den hade mer info om uppgiften jag försökte lösa. Jag använde Claude för att bättre förstå uppgiften genom att låta den läsa sidan direkt. Jag bad den också att inte lösa uppgiften, bara förklara. 

------------------------------------------------------------------------------

Övning 4

Övning 4 Claude: Had one problem where it was on the wrong branch (master), which still had the old scripts without the Övning 3 changes. Had to tell it to switch branch and re-plan with the updated script. Other than that no issues. It gave 3 questions on how to implement a multi-currency feature.  

Övning 4 OpenCode: No real problems. It also gave 3 clarifying questions up front (what "multiple currencies" should mean, where the rates come from, and which branch to use) before writing any code. I chose conversion with fixed rates, a hardcoded rate table in the module, and the med-opencode branch, so it built on top of the Övning 3 discount change instead of the outdated master script. It added the EXCHANGE_RATES table, a currency parameter defaulting to SEK, conversion applied after VAT, and raised ValueError on unknown currencies. It added 6 new tests and all 10 were green before it committed. It committed on the correct branch and only pushed after I explicitly asked.

Övning 4 Copilot: I asked it to switch to its branch and plan multi-currency support. It started on master, then switched to med-copilot and asked how currencies should work. I chose one currency per receipt (SEK, EUR, or USD), with no currency conversion. It planned first, then added currency selection to the CLI, SEK as the default for existing callers, validation for unsupported currencies, and the currency code in the displayed total. It updated the project guidance and added tests; all 10 tests passed. It committed on med-copilot and pushed only after I explicitly asked. The interaction also showed that the plan-mode handoff can start implementation automatically once the plan is approved.

The difference between just running and planning is the ability to inspect the changes before it starts, which allows you to have more control and insight about how it works.
I think planning mode is good when making big changes and when you want more control of what the AI is actually planning to do. For small commands, like for example, push to git, using planning mode is unnecessary. 


------------------------------------------------------------------------------