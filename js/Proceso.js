import {chromium} from "playwright";
import fs from "fs/promises";

(async () => {
    const input = process.argv;

    const navegador = await chromium.launch({
        headless: false
    });

    const contexto = await navegador.newContext();
    const pagina = await contexto.newPage();

    await pagina.goto('https://www.proceso.com.mx/noticias/buscar/?buscar='+input[2]);
    const texto_resultados = await pagina.textContent('div#alert-info')
    var regex = /(\d+)/g;
    const [numero_resultados, numeroPaginas] = texto_resultados.match(regex)
    var nPaginas = (numero_resultados/20)

    await pagina.waitForTimeout(20000);
    
    if(Number(nPaginas) > 5 ){
        nPaginas = 5
    }

    const noticias = []
    
    for (var i = 1; i <= nPaginas ; i++) {
        await pagina.waitForTimeout(5000);

        const info = await pagina.evaluate(() => {
            const items = document.querySelectorAll('div.caja div.row')
    
            const info = [...items].map((item) =>{
                const titulo = item.innerText
                const url = item.children[0].children[0].href   
    
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
        await pagina.getByText('Siguiente ').click()
        noticias.push(info)
    }

    fs.writeFile('noticias_Proceso.json', JSON.stringify(noticias, null, 2))

    //await contexto.close();
    await navegador.close();

})();