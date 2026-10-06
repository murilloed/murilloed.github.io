(() => {
  const buttons = [...document.querySelectorAll('[data-project-filter]')];
  const cards = [...document.querySelectorAll('.project-card')];
  const count = document.querySelector('#projects-count');
  const isPt = () => document.documentElement.lang.startsWith('pt');
  function updateCount() {
    if (count) {
      const n = cards.filter(card => !card.hidden).length;
      count.textContent = `${n} ${isPt() ? 'projetos' : 'projects'}`;
    }
  }
  buttons.forEach(button => button.addEventListener('click', () => {
    buttons.forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    cards.forEach(card => { card.hidden = button.dataset.projectFilter !== 'all' && card.dataset.category !== button.dataset.projectFilter; });
    updateCount();
  }));
  const budget = document.querySelector('#budget');
  function drawNetwork() {
    if (!budget) return;
    const edges = [[0,1,3],[0,2,2],[1,3,3],[2,4,2],[4,5,2],[3,5,4]];
    const demand = [0,30,10,70,20,80];
    const points = [[60,150],[220,60],[220,240],[400,60],[400,240],[540,150]];
    const limit = Number(budget.value);
    let best = { cost: 0, served: 0, mask: 0 };
    for (let mask = 0; mask < 64; mask++) {
      const cost = edges.reduce((total,e,i) => total + ((mask >> i) & 1 ? e[2] : 0), 0);
      if (cost > limit) continue;
      const reached = new Set([0]);
      for (let pass = 0; pass < 6; pass++) edges.forEach(([u,v],i) => {
        if (((mask >> i) & 1) && (reached.has(u) || reached.has(v))) { reached.add(u); reached.add(v); }
      });
      if (edges.some(([u,v],i) => ((mask >> i) & 1) && (!reached.has(u) || !reached.has(v)))) continue;
      const served = [...reached].reduce((total,i) => total + demand[i], 0);
      if (served > best.served || (served === best.served && cost < best.cost)) best = { cost, served, mask };
    }
    const svg = document.querySelector('#network-demo');
    svg.replaceChildren();
    function element(tag, attrs, text) {
      const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
      Object.entries(attrs).forEach(([k,v]) => node.setAttribute(k,String(v)));
      if (text !== undefined) node.textContent = text;
      svg.append(node);
    }
    edges.forEach(([u,v,c],i) => {
      const active = (best.mask >> i) & 1;
      element('line',{x1:points[u][0],y1:points[u][1],x2:points[v][0],y2:points[v][1],stroke:active?'#2de2e6':'#294058','stroke-width':active?5:2});
      element('text',{x:(points[u][0]+points[v][0])/2+7,y:(points[u][1]+points[v][1])/2-8,fill:'#b9cadc','font-size':14},c);
    });
    points.forEach(([x,y],i) => {
      element('circle',{cx:x,cy:y,r:20,fill:'#102b44',stroke:'#2de2e6','stroke-width':2});
      element('text',{x,y:y+5,fill:'#eaf3ff','text-anchor':'middle','font-size':13},i);
      element('text',{x,y:y+40,fill:'#b9cadc','text-anchor':'middle','font-size':12},`${isPt()?'demanda':'demand'} ${demand[i]}`);
    });
    document.querySelector('#budget-value').textContent = limit;
    document.querySelector('#network-result').textContent = isPt()
      ? `Demanda atendida: ${best.served} · Custo: ${best.cost} de ${limit} unidades sintéticas.`
      : `Served demand: ${best.served} · Cost: ${best.cost} of ${limit} synthetic units.`;
  }
  if (budget) budget.addEventListener('input',drawNetwork);
  new MutationObserver(() => { updateCount(); drawNetwork(); }).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});
  updateCount(); drawNetwork();
})();
