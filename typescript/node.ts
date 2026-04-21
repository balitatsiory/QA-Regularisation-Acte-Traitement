import { spawn } from 'child_process';

const data = {
   // nom: "Rakoto",
   // age: 25,
   // fichiers: ["a.tif", "b.tif"]
   acte_traitement: `['ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000137-01.tif',
'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000141-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000173-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000186-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000176-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000134-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000142-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000189-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000172-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000159-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000174-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000152-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000153-01.tif',
   'ANALAMANGA_Ambohidratrimo_Antehiroka_1981_TOME-01_N003_000139-01.tif']`
};

const py = spawn('python3', ['../python/app.py']);

// envoyer JSON à Python
py.stdin.write(JSON.stringify(data));
py.stdin.end();

// récupérer résultat
let result = '';

py.stdout.on('data', (chunk: Buffer) => {
   result += chunk.toString();
});

py.stdout.on('end', () => {
   try {
      const parsed = JSON.parse(result);
      console.log(parsed);
   } catch (err) {
      console.error("Erreur JSON:", result);
   }
});

// gestion erreur
py.stderr.on('data', (err: Buffer) => {
   console.error("Python error:", err.toString());
});