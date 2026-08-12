const q=document.getElementById("query"), province=document.getElementById("province"), btn=document.getElementById("searchBtn"), clear=document.getElementById("clearBtn"), results=document.getElementById("results"), title=document.getElementById("resultTitle"), meta=document.getElementById("resultMeta"), copyAll=document.getElementById("copyAll"); let current=[];
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
async function search(){
 const query=q.value.trim(), p=province.value;
 if(!query&&!p){renderEmpty("Ready to search","Enter a Khmer or English village name and press Search.");return}
 btn.disabled=true;btn.textContent="Searching…";
 try{
  const r=await fetch(`/api/search?q=${encodeURIComponent(query)}&province=${encodeURIComponent(p)}&limit=100`);
  const data=await r.json(); current=data.results||[];
  title.textContent=data.count?`${data.count} result${data.count===1?"":"s"} found`:"No results";
  meta.textContent=query?`Matches for “${query}”${p?` in ${p}`:""}`:(p?`All matching villages in ${p}`:"");
  copyAll.classList.toggle("hidden",!data.count); renderResults(current);
 }catch(e){renderEmpty("Something went wrong","Could not load the search results. Check that the Flask server is running.");}
 btn.disabled=false;btn.textContent="Search";
}
function renderEmpty(h,p){title.textContent="Search results";meta.textContent=p;copyAll.classList.add("hidden");results.innerHTML=`<div class="empty"><div class="empty-icon">⌕</div><h3>${esc(h)}</h3><p>${esc(p)}</p></div>`}
function renderResults(items){
 if(!items.length){results.innerHTML=`<div class="empty"><div class="empty-icon">⌕</div><h3>No village found</h3><p>Try another spelling, Khmer name, district, or code.</p></div>`;return}
 results.innerHTML=items.map((r,i)=>`<article class="result">
 <div class="result-top"><div><div class="village-kh">${esc(r.v_kh)}</div><div class="village-en">${esc(r.v_en)}</div></div><div class="code">${esc(r.code)}</div></div>
 <div class="address">${esc(r.address_kh)}</div>
 <div class="crumbs"><span>${esc(r.p_en)}</span><span>${esc(r.d_prefix)} ${esc(r.d_en)}</span><span>${esc(r.c_prefix)} ${esc(r.c_en)}</span></div>
 <div class="result-actions"><button class="copy-one" onclick="copyAddress(${i},this)">Copy Khmer address</button></div>
 </article>`).join("");
}
function copyAddress(i,el){navigator.clipboard.writeText(current[i].address_kh).then(()=>{const old=el.textContent;el.textContent="Copied ✓";setTimeout(()=>el.textContent=old,1200)})}
btn.addEventListener("click",search);q.addEventListener("keydown",e=>{if(e.key==="Enter")search()});q.addEventListener("input",()=>clear.classList.toggle("hidden",!q.value));clear.addEventListener("click",()=>{q.value="";clear.classList.add("hidden");q.focus()});copyAll.addEventListener("click",()=>{navigator.clipboard.writeText(current.map(r=>r.address_kh).join("\n"));copyAll.textContent="Copied ✓";setTimeout(()=>copyAll.textContent="Copy addresses",1200)});
fetch("/api/stats").then(r=>r.json()).then(s=>{document.getElementById("districtCount").textContent=s.districts.toLocaleString();document.getElementById("communeCount").textContent=s.communes.toLocaleString()});
