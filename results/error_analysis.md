# Error analysis

## (a) Cases only the LLM got right

**Example 1**

- corrupted: `Naime, kao metamorfmafus, ona je mogla da promeni svoj fizički izgled po volji, bez potrebe da koristi napitak lii čarolije.`
- original: `Naime, kao metamorfmafus, ona je mogla da promeni svoj fizički izgled po volji, bez potrebe da koristi napitak ili čarolije.`
- error: `lii` → should be `ili` (type: transposition)
- LLM predicted: `Naime, kao metamorfmafs, ona je mogla da promeni svoj fizički izgled po volji, bez potrebe da koristi napitak ili čarolije.`

**Example 2**

- corrupted: `Postojalo je od VI do X veka, kada je ušlo u sastavb jedinstvene Engleske države.`
- original: `Postojalo je od VI do X veka, kada je ušlo u sastav jedinstvene Engleske države.`
- error: `sastavb` → should be `sastav` (type: insertion)
- LLM predicted: `Postojalo je od VI do X veka, kada je ušlo u sastav jedinstvene Engleske države.`

**Example 3**

- corrupted: `Stalno savetuje Ivana da ne ini greške.`
- original: `Stalno savetuje Ivana da ne čini greške.`
- error: `ini` → should be `čini` (type: deletion)
- LLM predicted: `Stalno savetuje Ivana da ne čini greške.`

**Example 4**

- corrupted: `Molekul glukoze zasladjuje rastvor, a dijelovi glukoznih lanaca daju viskoznu konzistenciju.`
- original: `Molekul glukoze zaslađuje rastvor, a dijelovi glukoznih lanaca daju viskoznu konzistenciju.`
- error: `zasladjuje` → should be `zaslađuje` (type: diacritic)
- LLM predicted: `Molekul glukoze zaslađuje rastvor, a dijelovi glukoznih lanaca daju viskoznu konzistenciju.`

**Example 5**

- corrupted: `Anastasija je sledila svog sina, međutm uskoro se povukla iz javnog života i postala je opatica u Admont opatiji gde je ostala sve do svoje smrti.`
- original: `Anastasija je sledila svog sina, međutim uskoro se povukla iz javnog života i postala je opatica u Admont opatiji gde je ostala sve do svoje smrti.`
- error: `međutm` → should be `međutim` (type: deletion)
- LLM predicted: `Anastasija je sledila svog sina, međutim uskoro se povukla iz javnog života i postala je opatica u Admont opatiji, gde je ostala sve do svoje smrti.`

**Example 6**

- corrupted: `Nakon rata se u seno vratilo manje od stotinu ljudi, uglavnom starijih osoba.`
- original: `Nakon rata se u selo vratilo manje od stotinu ljudi, uglavnom starijih osoba.`
- error: `seno` → should be `selo` (type: substitution)
- LLM predicted: `Nakon rata se u selo vratilo manje od stotinu ljudi, uglavnom starijih osoba.`

**Example 7**

- corrupted: `Marina Nikola je medju prvima 1927.`
- original: `Marina Nikola je među prvima 1927.`
- error: `medju` → should be `među` (type: diacritic)
- LLM predicted: `Marina Nikola je među prvimama 1927.`

**Example 8**

- corrupted: `Tipične analize su analize prolaznih podataka za pravljenje upotrebno-definisanih lanaca, zavisnih analiza, alijas analiza, pokaznih analiza, iskejp analiza ird.`
- original: `Tipične analize su analize prolaznih podataka za pravljenje upotrebno-definisanih lanaca, zavisnih analiza, alijas analiza, pokaznih analiza, iskejp analiza itd.`
- error: `ird` → should be `itd` (type: substitution)
- LLM predicted: `Tipične analize su analize prolaznih podataka za pravljenje upotrebno-definisanih lanaca, zavisnih analiza, alijas analiza, pokaznih analiza, escape analiza itd.`

**Example 9**

- corrupted: `Potom se tesko razboleo i celo telo mu je bilo pokriveno ranama od temena do tabana.`
- original: `Potom se teško razboleo i celo telo mu je bilo pokriveno ranama od temena do tabana.`
- error: `tesko` → should be `teško` (type: diacritic)
- LLM predicted: `Potom se teško razboleo i celo telo mu je bilo pokriveno ranama od temena do tabana.`

**Example 10**

- corrupted: `Alat je prvobitno nosio ime Worldcraft, dok ga je Ben Moris nezavisno razvijao, pre nego sto ga je Valv otkupio.`
- original: `Alat je prvobitno nosio ime Worldcraft, dok ga je Ben Moris nezavisno razvijao, pre nego što ga je Valv otkupio.`
- error: `sto` → should be `što` (type: diacritic)
- LLM predicted: `Alat je prvobitno nosio ime Worldcraft, dok ga je Ben Moris nezavisno razvijao, pre nego što ga je Valv otkupio.`


## (b) Cases the n-gram model fixed but Approach 1 (Norvig) got wrong

**Example 1**

- corrupted: `Naziv Stari Vlab se odnosi na Latine, a ne na Vlahe (narod).`
- original: `Naziv Stari Vlah se odnosi na Latine, a ne na Vlahe (narod).`
- error: `Vlab` → should be `Vlah` (type: substitution)
- Norvig predicted: `Slab`
- N-gram predicted: `Vlah`

**Example 2**

- corrupted: `Grnčarija ovog porekla ima nesumnjivu estetsku vrednost, a posebno sudovi u oblikg životinjskih figura.`
- original: `Grnčarija ovog porekla ima nesumnjivu estetsku vrednost, a posebno sudovi u obliku životinjskih figura.`
- error: `oblikg` → should be `obliku` (type: substitution)
- Norvig predicted: `oblik`
- N-gram predicted: `obliku`

**Example 3**

- corrupted: `Ustanova je počela sa radm 2. oktobra 1969.`
- original: `Ustanova je počela sa radom 2. oktobra 1969.`
- error: `radm` → should be `radom` (type: deletion)
- Norvig predicted: `radi`
- N-gram predicted: `radom`

**Example 4**

- corrupted: `Uglavnom je sivo-plave boje, dok su krila smeđa sa crim mrljama.`
- original: `Uglavnom je sivo-plave boje, dok su krila smeđa sa crnim mrljama.`
- error: `crim` → should be `crnim` (type: deletion)
- Norvig predicted: `rim`
- N-gram predicted: `crnim`

**Example 5**

- corrupted: `Precesija je tendencija žiroskopa da se zaokrene pod praim uglom prema ulaznoj sili poremećaja.`
- original: `Precesija je tendencija žiroskopa da se zaokrene pod pravim uglom prema ulaznoj sili poremećaja.`
- error: `praim` → should be `pravim` (type: deletion)
- Norvig predicted: `prvim`
- N-gram predicted: `pravim`

**Example 6**

- corrupted: `Međutim, ukradeni instrumenti se često budu pronađeni, nakon što su vođeni kao nestali duig niz godina.`
- original: `Međutim, ukradeni instrumenti se često budu pronađeni, nakon što su vođeni kao nestali dugi niz godina.`
- error: `duig` → should be `dugi` (type: transposition)
- Norvig predicted: `dug`
- N-gram predicted: `dugi`

**Example 7**

- corrupted: `Nauka koja proučava vrednosti naziav se aksiologija.`
- original: `Nauka koja proučava vrednosti naziva se aksiologija.`
- error: `naziav` → should be `naziva` (type: transposition)
- Norvig predicted: `naziv`
- N-gram predicted: `naziva`

**Example 8**

- corrupted: `Menjanje nalepnica u Braziu na Svetskom prvenstvu 2018.`
- original: `Menjanje nalepnica u Brazilu na Svetskom prvenstvu 2018.`
- error: `Braziu` → should be `Brazilu` (type: deletion)
- Norvig predicted: `Brazil`
- N-gram predicted: `Brazilu`

**Example 9**

- corrupted: `Teo postaje pravi frajet.`
- original: `Teo postaje pravi frajer.`
- error: `frajet` → should be `frajer` (type: substitution)
- Norvig predicted: `frajt`
- N-gram predicted: `frajer`

**Example 10**

- corrupted: `Da bi se prilagodila ovim promenama, birokratija je bila proširena i raznovrsna, da bi imala mnogo veću ulogu u upravj carstva.`
- original: `Da bi se prilagodila ovim promenama, birokratija je bila proširena i raznovrsna, da bi imala mnogo veću ulogu u upravi carstva.`
- error: `upravj` → should be `upravi` (type: substitution)
- Norvig predicted: `upravo`
- N-gram predicted: `upravi`


## (c) Cases everything failed on

**Example 1**

- corrupted: `Bio je i potpredsednik tv.`
- original: `Bio je i potpredsednik tzv.`
- error: `tv` → should be `tzv` (type: deletion)
- predictions: norvig=`(unchanged)`, ngram=`(unchanged)`, llm=`(unchanged)`

**Example 2**

- corrupted: `Osnovni zahtevi u Nemačkoj ticali su se garantija prava građama, donošenja ustava i ujedinjenja Nemačke na federalnim osnovama.`
- original: `Osnovni zahtevi u Nemačkoj ticali su se garantija prava građana, donošenja ustava i ujedinjenja Nemačke na federalnim osnovama.`
- error: `građama` → should be `građana` (type: substitution)
- predictions: norvig=`(unchanged)`, ngram=`(unchanged)`, llm=`građanima`

**Example 3**

- corrupted: `Ova dvojica slikara, potpuno različitih umetničkih shvatanja, prvi put su se sreli kao saradnici na izradi ikona za duvošku crkvu.`
- original: `Ova dvojica slikara, potpuno različitih umetničkih shvatanja, prvi put su se sreli kao saradnici na izradi ikona za divošku crkvu.`
- error: `duvošku` → should be `divošku` (type: substitution)
- predictions: norvig=`devojku`, ngram=`duboku`, llm=``

**Example 4**

- corrupted: `Takmičarke čija su iena podebljana učestvuju na EP 1996.`
- original: `Takmičarke čija su imena podebljana učestvuju na EP 1996.`
- error: `iena` → should be `imena` (type: deletion)
- predictions: norvig=`(unchanged)`, ngram=`(unchanged)`, llm=`jedna`

**Example 5**

- corrupted: `Godine 2001, objavljen je album Pišanje uz vetar na kome su se našle pesme kao što su Sbin je lud, Ljubav ovde više ne stanuje, Daj mi lovu itd.`
- original: `Godine 2001, objavljen je album Pišanje uz vetar na kome su se našle pesme kao što su Srbin je lud, Ljubav ovde više ne stanuje, Daj mi lovu itd.`
- error: `Sbin` → should be `Srbin` (type: deletion)
- predictions: norvig=`Sin`, ngram=`Sin`, llm=`Šbin`

**Example 6**

- corrupted: `Radi honorarno u butiku obuće Gles sbiper.`
- original: `Radi honorarno u butiku obuće Gles sliper.`
- error: `sbiper` → should be `sliper` (type: substitution)
- predictions: norvig=`skiper`, ngram=`biper`, llm=`Schuhber`

**Example 7**

- corrupted: `Bend je počeo sa svirkom i onda se iz pozadine, kao deus ex machna cuo bubanj.`
- original: `Bend je počeo sa svirkom i onda se iz pozadine, kao deus ex machna čuo bubanj.`
- error: `cuo` → should be `čuo` (type: diacritic)
- predictions: norvig=`(unchanged)`, ngram=`(unchanged)`, llm=``

**Example 8**

- corrupted: `Takođe se i pominje „pop sin Cujica”, a takođe i „`
- original: `Takođe se i pominje „pop sin Vujica”, a takođe i „`
- error: `Cujica` → should be `Vujica` (type: substitution)
- predictions: norvig=`Bujica`, ngram=`Šujica`, llm=`(unchanged)`

**Example 9**

- corrupted: `Potenciometar radi na principu uravnoteženja nepoznatog napona nasuprot poznatom naponu u osnom spoju.`
- original: `Potenciometar radi na principu uravnoteženja nepoznatog napona nasuprot poznatom naponu u mosnom spoju.`
- error: `osnom` → should be `mosnom` (type: deletion)
- predictions: norvig=`(unchanged)`, ngram=`(unchanged)`, llm=`(unchanged)`

**Example 10**

- corrupted: `U slučaju da selekcija Rusije kao domaćin narednog turnira zauzme jednu od dve poslednje pozicije umesto njih u nizi rang takmičenja ispala bi 14. plasirana selekcija.`
- original: `U slučaju da selekcija Rusije kao domaćin narednog turnira zauzme jednu od dve poslednje pozicije umesto njih u niži rang takmičenja ispala bi 14. plasirana selekcija.`
- error: `nizi` → should be `niži` (type: diacritic)
- predictions: norvig=`(unchanged)`, ngram=`(unchanged)`, llm=`nizu`


## (d) LLM overcorrections (changed an originally-correct word)

**Example 1**

- corrupted: `Naime, kao metamorfmafus, ona je mogla da promeni svoj fizički izgled po volji, bez potrebe da koristi napitak lii čarolije.`
- original: `Naime, kao metamorfmafus, ona je mogla da promeni svoj fizički izgled po volji, bez potrebe da koristi napitak ili čarolije.`
- LLM changed correct word: `metamorfmafus` → `metamorfmafs`
- LLM predicted: `Naime, kao metamorfmafs, ona je mogla da promeni svoj fizički izgled po volji, bez potrebe da koristi napitak ili čarolije.`

**Example 2**

- corrupted: `Osnovni zahtevi u Nemačkoj ticali su se garantija prava građama, donošenja ustava i ujedinjenja Nemačke na federalnim osnovama.`
- original: `Osnovni zahtevi u Nemačkoj ticali su se garantija prava građana, donošenja ustava i ujedinjenja Nemačke na federalnim osnovama.`
- LLM changed correct word: `garantija` → `garancija`
- LLM predicted: `Osnovni zahtevi u Nemačkoj ticali su se garancija prava građanima, donošenja ustava i ujedinjenja Nemačke na federalnim osnovama.`

**Example 3**

- corrupted: `Sada većina brodova ima unutrašnji motor s unutrašnjim sagorijevanjem koristeći blqago refinirani tip petroleja zvani bunker gorivo.`
- original: `Sada većina brodova ima unutrašnji motor s unutrašnjim sagorijevanjem koristeći blago refinirani tip petroleja zvani bunker gorivo.`
- LLM changed correct word: `koristeći` → `koji koristi blago`
- LLM predicted: `Sada većina brodova ima unutrašnji motor s unutrašnjim sagorijevanjem koji koristi blago refinirani tip petroleja zvan bunker gorivo.`

**Example 4**

- corrupted: `Njihovo stavljanje u promet uskalđeno je sa Zakonom o biocidnim proizvodima, čije sprovođenje kontroliušu Agencije za hemikalije zemalja koje su taj zakon donele.`
- original: `Njihovo stavljanje u promet uskalđeno je sa Zakonom o biocidnim proizvodima, čije sprovođenje kontrolišu Agencije za hemikalije zemalja koje su taj zakon donele.`
- LLM changed correct word: `uskalđeno` → `usklađeno`
- LLM predicted: `Njihovo stavljanje u promet usklađeno je sa Zakonom o biocidnim proizvodima, čije sprovođenje kontrolišu Agencije za hemikalije zemalja koje su taj zakon donele.`

**Example 5**

- corrupted: `Poslednja faza bitke odigrala se u podnožiju brda, u dolini reke Morave, gde su se Srbi utvridli u dolini uz reku sa namerom da kontrolišu prelaze na reci.`
- original: `Poslednja faza bitke odigrala se u podnožiju brda, u dolini reke Morave, gde su se Srbi utvrdili u dolini uz reku sa namerom da kontrolišu prelaze na reci.`
- LLM changed correct word: `podnožiju` → `podnožju`
- LLM predicted: `Poslednja faza bitke odigrala se u podnožju brda, u dolini reke Morave, gde su se Srbi utvrdili u dolini uz reku sa namerom da kontrolišu prelaze na reci.`

**Example 6**

- corrupted: `Razvijač Afdvanced Warfare-a je kompanija Sledgehamer gejms.`
- original: `Razvijač Advanced Warfare-a je kompanija Sledgehamer gejms.`
- LLM changed correct word: `Sledgehamer` → `Sledgehammer`
- LLM predicted: `Razvijač Advanced Warfare-a je kompanija Sledgehammer Games.`

**Example 7**

- corrupted: `Marina Nikola je medju prvima 1927.`
- original: `Marina Nikola je među prvima 1927.`
- LLM changed correct word: `prvima` → `prvimama`
- LLM predicted: `Marina Nikola je među prvimama 1927.`

**Example 8**

- corrupted: `Tipične analize su analize prolaznih podataka za pravljenje upotrebno-definisanih lanaca, zavisnih analiza, alijas analiza, pokaznih analiza, iskejp analiza ird.`
- original: `Tipične analize su analize prolaznih podataka za pravljenje upotrebno-definisanih lanaca, zavisnih analiza, alijas analiza, pokaznih analiza, iskejp analiza itd.`
- LLM changed correct word: `iskejp` → `escape`
- LLM predicted: `Tipične analize su analize prolaznih podataka za pravljenje upotrebno-definisanih lanaca, zavisnih analiza, alijas analiza, pokaznih analiza, escape analiza itd.`

**Example 9**

- corrupted: `U mestu je pravoslavna Vazneenska crkva, pri kojoj služe parosi Toma Bogdanović i Toma Lazić.`
- original: `U mestu je pravoslavna Vaznesenska crkva, pri kojoj služe parosi Toma Bogdanović i Toma Lazić.`
- LLM changed correct word: `parosi` → `parohi`
- LLM predicted: `U mestu je pravoslavna Vaznesenska crkva, pri kojoj služe parohi Toma Bogdanović i Toma Lazić.`

**Example 10**

- corrupted: `Na konkurs su primani laki potpnuo metalni avioni.`
- original: `Na konkurs su primani laki potpuno metalni avioni.`
- LLM changed correct word: `primani` → `primljeni`
- LLM predicted: `Na konkurs su primljeni laki potpuni metalni avioni.`

