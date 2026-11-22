import fs from 'fs'; import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const SKC = require('/home/user/leokmei-girsa/tools/sakem_core.js');
const caps = JSON.parse(fs.readFileSync('_work/p76/caps.json', 'utf8'));
caps.forEach((c, k) => { const t = SKC.toInter(c.packet.units).text; fs.writeFileSync('_work/p76/p' + (k + 1) + '.txt', t); console.log(c.perek, c.title, c.packet.units.length, t.split('\n').length); });
