const data={
 presidente:[['Carlos Silva','PARTIDO A','38,4%','38.4'],['Mariana Santos','PARTIDO B','32,7%','32.7'],['Roberto Lima','PARTIDO C','18,6%','18.6']],
 governador:[['Ana Costa','PARTIDO B','42,1%','42.1'],['Paulo Mendes','PARTIDO A','28,9%','28.9'],['Fernanda Alves','PARTIDO D','15,3%','15.3']],
 senador:[['João Ribeiro','PARTIDO C','31,5%','31.5'],['Camila Duarte','PARTIDO A','27,8%','27.8'],['Eduardo Nunes','PARTIDO B','19,4%','19.4']]
};
function renderPanel(id,title,rows){document.getElementById(id).innerHTML=`<div class="section-title"><span>${title==='PRESIDENTE'?'▥':title==='GOVERNADOR'?'♣':'♟'}</span> ${title}<em class="demo">DADOS DE DEMONSTRAÇÃO</em></div>${rows.map((r,i)=>`<div class="candidate"><span class="rank">${i+1}º</span><span class="avatar">${r[0][0]}</span><div><div class="candidate-name">${r[0]}</div><div class="party">${r[1]}</div></div><div><div class="pct">${r[2]}</div><div class="bar"><span style="width:${Math.min(parseFloat(r[3])*2,100)}%"></span></div></div></div>`).join('')}<a class="ranking" href="#">Ver ranking completo →</a>`}
renderPanel('presidente-panel','PRESIDENTE',data.presidente);renderPanel('governador-panel','GOVERNADOR',data.governador);renderPanel('senador-panel','SENADOR',data.senador);
const updates=[['18:42','SP','72,3%'],['18:40','MG','69,1%'],['18:37','PR','66,4%'],['18:35','BA','58,7%'],['18:33','RJ','71,2%'],['18:31','RS','64,9%'],['18:28','GO','61,5%'],['18:25','PE','55,4%']];
document.getElementById('updates').innerHTML=updates.map(u=>`<div class="update"><span class="time">${u[0]}</span><span class="uf-name">⌖ ${u[1]}</span><span><b class="up">↑</b> Seções totalizadas ${u[2]}</span></div>`).join('');
document.querySelectorAll('.nav-tabs button[data-cargo]').forEach(btn=>btn.addEventListener('click',()=>{document.querySelectorAll('.nav-tabs button').forEach(b=>b.classList.remove('tab-active'));btn.classList.add('tab-active')}));
