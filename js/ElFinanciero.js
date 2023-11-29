import {chromium} from "playwright";
import fs from "fs/promises";

(async () => {
    const input = process.argv;

    const navegador = await chromium.launch({
        headless: false
    });

    const contexto = await navegador.newContext();
    const pagina = await contexto.newPage();

    await pagina.goto('https://www.elfinanciero.com.mx/queryly-advanced-search/?query='+input[2]);
    await pagina.waitForTimeout(10000);
    await pagina.click('#sortby')
    await pagina.locator('select').selectOption('date');
    await pagina.waitForTimeout(20000);
    //await pagina.waitForSelector('#queryly_advanced_container')
    const texto_resultados = await pagina.textContent('div.result_count')
    const numero_resultados = texto_resultados.split(' ')[1]
    var numeroPaginas = (numero_resultados/20)

    await pagina.waitForTimeout(5000);
    
    if(Number(numeroPaginas) > 5 ){
        numeroPaginas = 5
    }

    const noticias = []
    
    for (var i = 1; i <= numeroPaginas ; i++) {
        await pagina.waitForTimeout(5000);
        const info = await pagina.evaluate(() => {
            const items = document.querySelectorAll('div.queryly_item_row a')

            const info = [...items].map((item) =>{
                const titulo = item.textContent
                const url = item.href  

                var regex = /(\d+)/g;
                let [anno, mes, dia] = url.match(regex)
                const fecha = (anno +'/'+ mes +'/'+ dia)

                if (anno >= 2020) {
                    return {
                        titulo,
                        url,
                        fecha
                    }
                }
                
            });

            return info
        })

        //console.log(i)
        await pagina.click('a.next_btn')
        noticias.push(info)
    }

    fs.writeFile('noticias_ElFinanciero.json', JSON.stringify(noticias, null, 2))

    //await contexto.close();
    await navegador.close();

})();