import puppeteer from "puppeteer";
import {chromium} from "playwright";
import fs from "fs/promises";

(async () => {
    const input = process.argv;

    const navegador = await chromium.launch({
        headless: false
    });

    const contexto = await navegador.newContext();
    const pagina = await contexto.newPage();

    await pagina.goto('https://www.animalpolitico.com/buscador');
    await pagina.getByRole('textbox').fill(input[2])
    await pagina.click('button[type=submit]')
    await pagina.waitForTimeout(30000);
    //await pagina.waitForSelector('div.grid')

    const info_paginas = await pagina.evaluate(() => { 
        const paginacion = document.querySelectorAll('li.mx-1 a')
        const paginas =  paginacion[3].textContent
        return paginas
    })

    const noticias = []

    for (var i = 1; i < info_paginas ; i++) {
        await pagina.waitForTimeout(15000);

        const info = await pagina.evaluate(() => {
            const items = document.querySelectorAll('div.col-span-12.flex a')

            const data = [...items].map((item) => {
                
                const titulo = item.textContent
                const url = item.href  

                return {
                    titulo,
                    url
                }
            });
            return data

        })
        
        //console.log(i)
        await pagina.click('li.next')
        noticias.push(info)
    }

    //console.log(noticias)

    fs.writeFile('noticias_Animal_Politico.json', JSON.stringify(noticias, null, 2))

    await navegador.close();

})();