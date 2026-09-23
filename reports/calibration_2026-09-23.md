# Modelwatch judge calibration

Date: 2026-09-23
Run: 20260923T083904+0200

Score each completion from 1 to 5 using its rubric. Leave the judge score unchanged.
Task prompts are intentionally excluded.

## 1. dutch.btw_source

Model: `anthropic/claude-sonnet-4-5-20250929`
Judge model: `openrouter/openai/gpt-5.2`
Judge score: 1.00
Human score: 1.00

Rubric: Beoordeel beide teksten van 1 tot 5. Een 5 zegt 15 februari, noemt Belastingdienst.nl als officiële bron en legt uit dat bij te late verzending de uiterste factuurdatum bepaalt in welk tijdvak de btw moet worden aangegeven. Een 1 noemt een andere termijn, mist de bron of koppelt de aangifte zonder voorbehoud aan de verzenddatum.

Completion:

````text
# Kort antwoord
Uiterlijk **28 februari** (de 15e van de maand volgend op de maand waarin de dienst is verricht).

## Officiële bron
**Artikel 35, lid 1 van de Wet op de omzetbelasting 1968** en **artikel 35a van de Uitvoeringsbeschikking omzetbelasting 1968**.

## BTW-aangifte bij te late facturering

Als de factuur te laat wordt verstuurd (dus na 28 februari), moet de btw worden aangegeven in het **tijdvak waarin de dienst is verricht** (januari), **niet** in het tijdvak waarin de factuur daadwerkelijk wordt verstuurd.

De btw is namelijk verschuldigd op het moment dat:
- De dienst is verricht, of
- De factuur wordt uitgereikt

**Wat het eerst plaatsvindt** is bepalend. Omdat de dienst op 28 januari is verricht, is dat het moment waarop de btw verschuldigd wordt en dus in de aangifte over januari (of Q1 bij kwartaalaangifte) moet worden opgenomen - ongeacht wanneer de factuur daadwerkelijk wordt verstuurd.
````

## 2. dutch.correct_errors

Model: `openrouter/qwen/qwen3.5-plus-02-15`
Judge model: `anthropic/claude-opus-4-5-20251101`
Judge score: 4.50
Human score: 4.80

Rubric: Beoordeel beide teksten van 1 tot 5. Een 5 corrigeert precies de vijf grammaticale en spellingfouten, introduceert geen nieuwe fout en verandert geen betekenis. Een 1 laat fouten staan, herschrijft onnodig veel of verandert de technische claim.

Completion:

````text
De agent draait elke nacht. De resultaten worden niet gecontroleerd. Zij hebben de deployment getest, en het betekent dat de pipeline stabieler is dan gisteren.
````

## 3. dutch.formal_email

Model: `anthropic/claude-sonnet-4-5-20250929`
Judge model: `openrouter/openai/gpt-5.2`
Judge score: 4.00
Human score: 4.50

Rubric: Beoordeel beide teksten van 1 tot 5. Een 5 gebruikt consequent u en uw, vraagt direct om toestemming, noemt anonimisering, opslag in Nederland, verwijdering na 30 dagen, geen klantnamen en de datum 2 oktober. De toon is formeel en sober, met de vaste tweetalige afsluiting. Een 1 mengt aanspreekvormen, verstopt het verzoek of maakt ongefundeerde veiligheidsclaims.

Completion:

````text
**Onderwerp:** Verzoek tot toestemming gebruik geanonimiseerde procesbeschrijvingen voor adviesonderzoek

Geachte heer/mevrouw [Achternaam],

Bij deze doe ik een beroep op uw medewerking voor een adviesonderzoek dat ik momenteel uitvoer.

In het kader van dit onderzoek zou ik graag gebruik willen maken van twee geanonimiseerde procesbeschrijvingen uit uw organisatie. Deze documenten zouden mij helpen om een gedegen analyse te maken en tot waardevolle aanbevelingen te komen.

Ik wil u graag de volgende garanties bieden met betrekking tot de verwerking van deze documenten:
- Alle bestanden blijven binnen Nederland en worden niet gedeeld met derden
- De documenten bevatten geen klantnamen of andere direct herleidbare informatie
- Alle bestanden worden binnen 30 dagen na afronding van het onderzoek definitief verwijderd

Ik zou het zeer op prijs stellen indien u mij toestemming zou willen verlenen voor het gebruik van deze procesbeschrijvingen. Mocht u aanvullende voorwaarden of waarborgen wensen, dan hoor ik dit uiteraard graag.

Ik verzoek u vriendelijk om mij vóór 2 oktober van uw beslissing op de hoogte te stellen, zodat ik mijn onderzoeksplanning hierop kan afstemmen.

Voor eventuele vragen of nadere toelichting kunt u mij uiteraard bereiken via onderstaande contactgegevens.

Bij voorbaat dank voor uw tijd en overweging.

Met vriendelijke groet,

[Uw volledige naam]
[Uw functie/organisatie]
[Telefoonnummer]
[E-mailadres]
````

## 4. dutch.translate_terms

Model: `openrouter/qwen/qwen3.5-plus-02-15`
Judge model: `anthropic/claude-opus-4-5-20251101`
Judge score: 5.00
Human score: 5.00

Rubric: Beoordeel beide teksten van 1 tot 5. Een 5 behoudt agent, pipeline, token en deployment exact, vertaalt beide zinnen volledig, houdt het onderscheid tussen releasecontrole en applicatiecorrectheid intact en leest als natuurlijk technisch Nederlands. Een 1 vertaalt de vaste termen, verliest de ontkenning of maakt van de controle een bewijs van correctheid.

Completion:

````text
De agent controleert elke pipeline-stap voor de deployment. Een mislukte token-controle stopt de release, maar het bewijst niet dat de applicatie zelf correct is.
````

## 5. voice.covering_email_nl

Model: `anthropic/claude-sonnet-4-5-20250929`
Judge model: `openrouter/openai/gpt-5.2`
Judge score: 2.00
Human score: 2.50

Rubric: Beoordeel beide teksten van 1 tot 5. Een 5 geeft de conclusie in de eerste regel, gebruikt consequent je of jullie, noemt de 50 dossiers en de vertraging van twee weken, stelt één concrete vraag, blijft binnen drie korte alinea's en gebruikt de vaste tweetalige afsluiting. Een 1 mengt u en je, verstopt het advies of klinkt als verkooptekst.

Completion:

````text
Onderwerp: Adviesmemo modelkeuze + vervolgafspraak

Beste [naam],

Zoals besproken stuur ik je hierbij het adviesmemo over de modelkeuze.

De conclusie: ik adviseer om de definitieve keuze twee weken uit te stellen en eerst 50 echte dossiers te meten. Dit geeft ons een veel solider basis voor de beslissing. Het nadeel is wel dat de pilot hierdoor twee weken opschuift.

Graag zou ik donderdag 30 minuten met je inplannen om de meetset vast te leggen, zodat we daarna direct aan de slag kunnen.

Laat je weten of donderdag schikt? Dan stuur ik een uitnodiging.

Groet,
[naam]
````

## 6. voice.critical_reply_nl

Model: `openrouter/qwen/qwen3.5-plus-02-15`
Judge model: `anthropic/claude-opus-4-5-20251101`
Judge score: 3.00
Human score: 3.50

Rubric: Beoordeel beide teksten van 1 tot 5. Een 5 erkent direct dat twee modellen geen marktclaim dragen, noemt 30 taken en vijf herhalingen, maakt duidelijk wat de meting wel bewijst, noemt de zes modellen van volgende maand en blijft kalm. Een 1 valt de reageerder aan, overschrijft de beperking of gebruikt lege beleefdheid.

Completion:

````text
Bedankt voor je scherpe observatie. Je hebt gelijk: twee modellen zijn te weinig voor een definitieve marktclaim. Dat is ook waarom we het in het artikel expliciet een 'eerste meting' noemen.

Om binnen deze scope toch zo robuust mogelijke data te verzamelen, zijn er 30 taken en vijf herhalingen gebruikt. We zijn het er echter mee eens dat een volwaardige benchmark meer vergelijkingsmateriaal vraagt. Daarom voegen we volgende maand zes extra modellen toe aan de test. We waarderen je feedback; het helpt ons om de verwachtingen helder te houden.
````

## 7. voice.linkedin_en

Model: `anthropic/claude-sonnet-4-5-20250929`
Judge model: `openrouter/openai/gpt-5.2`
Judge score: 3.00
Human score: 3.00

Rubric: Score both texts from 1 to 5. A 5 puts the measured claim in line one, gives numbers and method early, explains the mechanism, admits the discarded run and interactive-chat limit, avoids a LinkedIn sentence ladder, ends on a specific reframe, and includes the requested disclosure. A 1 uses generic promotion, omits provenance, or turns the result into a universal claim.

Completion:

````text
# Prompt Caching: A Real-World Test with Surprising Results

I recently ran an experiment to measure the impact of prompt caching on our AI workflows, and the numbers are compelling.

**The Setup:**
Over four weekly runs, I processed the same 30 recurring tasks that our team handles regularly. The cache setup took 55 minutes initially—a small upfront investment that paid off quickly.

**The Results:**
With prompt caching enabled, our weekly token input dropped from 18.4 million to just 4.7 million tokens. That's a 74% reduction in input tokens, which translates directly to cost savings and faster processing times.

**The Reality Check:**
One of my weekly runs had to be discarded entirely because the provider changed its backend mid-experiment—a good reminder that we're building on evolving infrastructure. Also important to note: this method works brilliantly for repetitive, batch-style tasks, but I haven't seen the same dramatic savings for interactive chat sessions where context varies significantly.

**Key Takeaway:**
If your AI workflows involve recurring tasks with consistent prompts—think weekly reports, standardized analyses, or batch processing—prompt caching is worth implementing. The setup time is minimal, and the savings compound quickly.

For teams running variable, conversational AI applications, your mileage will vary. Test it with your specific use case.

Has anyone else experimented with prompt caching? I'd love to hear about your results and use cases.

---
*Disclosure: AI helped draft the outline for this post; the measurements and conclusions are my own.*
````

## 8. voice.rewrite_en

Model: `openrouter/qwen/qwen3.5-plus-02-15`
Judge model: `anthropic/claude-opus-4-5-20251101`
Judge score: 3.00
Human score: 3.00

Rubric: Score both texts from 1 to 5. A 5 opens with the result, preserves all numbers and causes, explains why the failed deployment matters, names the fixture limitation, uses plain B2 English, varies sentence length, and avoids sales language. A 1 loses facts, oversells autonomy, or hides the failure and limitation.

Completion:

````text
In 6 hours, our internal coding agent produced 14 commits with no human code changes and passed 41 tests, though the first deployment attempt failed because the release token was read-only. The only remaining risk is that the test fixtures cover only one customer configuration.
````

## 9. voice.tighten_nl

Model: `anthropic/claude-sonnet-4-5-20250929`
Judge model: `openrouter/openai/gpt-5.2`
Judge score: 4.50
Human score: 4.50

Rubric: Beoordeel beide teksten van 1 tot 5. Een 5 is maximaal half zo lang, behoudt 24 runs, 7,2 minuten, drie time-outs, de externe API, 8 GB en de onzekerheid voor grotere datasets. Het resultaat is direct, natuurlijk Nederlands. Een 1 verliest een feit, verbergt de mislukte runs of voegt een bredere claim toe.

Completion:

````text
'Na evaluatie van 24 runs is de nieuwe pipeline gemiddeld 7,2 minuten sneller dan de bestaande. Wel faalden 3 runs door API time-outs. De meting op één dataset van 8 GB laat onzeker of dit verschil bij grotere datasets blijft bestaan.'
````

## 10. voice.tldr_en

Model: `openrouter/qwen/qwen3.5-plus-02-15`
Judge model: `anthropic/claude-opus-4-5-20251101`
Judge score: 5.00
Human score: 5.00

Rubric: Score both texts from 1 to 5. A 5 gives the recommendation first, keeps the costs, accuracy, sample size, and historical-data limit, then states what evidence would change the recommendation. It uses exactly two concise sentences and plain English. A 1 hides the recommendation, drops the trade-off, or invents certainty.

Completion:

````text
We recommend the cheapest pipeline (EUR 38, 82% accuracy) for the pilot based on 1,200 historical questions, rather than the EUR 121 option with 89% accuracy. This recommendation would change if the pilot requires handling new product areas, as the evaluation did not test performance on unseen topics.
````
