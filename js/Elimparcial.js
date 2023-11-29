import {chromium} from "playwright";
import fs from "fs/promises";

(async () => {
    const input = process.argv;

    const navegador = await chromium.launch({
        headless: false
    });

    const contexto = await navegador.newContext();
    const pagina = await contexto.newPage();

    await pagina.goto('https://www.elimparcial.com/buscar.html?search='+input[2]);
    const texto_resultados = await pagina.textContent('h3.section__title')
    await pagina.waitForTimeout(10000);
    var regex = /(\d+)/g;
    const [numero_resultados] = texto_resultados.match(regex)
    const numeroPaginas = (numero_resultados/9)
    
    for (var i = 1; i <= numeroPaginas ; i++) {
        await pagina.waitForTimeout(4000);
        await pagina.click('button.viewmore__button')
    }

    const info = await pagina.evaluate(() => {
        const items = document.querySelectorAll('div.row__container div.news__data')

        const info = [...items].map((item) =>{
            const titulo = item.outerText
            const url = item.children[1].lastElementChild.href  
            const fecha = item.lastElementChild.innerText

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

    fs.writeFile('noticias_El_Imparcial.json', JSON.stringify(info, null, 2))

    //await contexto.close();
    await navegador.close();

})();