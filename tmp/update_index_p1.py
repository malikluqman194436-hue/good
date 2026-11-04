import sys

path = 'app/src/main/assets/index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update makeSpikes heights and spike object
old_make_spikes = '''function makeSpikes(len, lvl, top, bot, noSpikes = false, levelRng) {
  const count = Math.ceil(len / 12);
  const heights = { small: 12, medium: 22, big: 36 };
  const L = lvl || curLevel;
  const stage = getStageNumber(L);
  const allowMixed = (stage >= 3);
  const mixedProbability = (stage === 3) ? 0.20 : 0.35;

  function gen(isTop) {
    const list = [];
    let i = 0;
    while (i < count) {
      const cLen = Math.min(count - i, Math.floor(2 + levelRng() * 4));
      const baseSize = pickClusterSize(L, levelRng);
      const isMixed = allowMixed && (levelRng() < mixedProbability);

      for (let k = 0; k < cLen; k++) {
        let size = baseSize;
        if (isMixed && k % 2 === 1) {
          size = (baseSize === 'big') ? 'medium' : 'small';
        }
        const h = noSpikes ? 0 : heights[size];
        list.push({ h, size });
      }
      i += cLen;
    }
    return list;
  }
  const topSpikes = gen(true);
  const botSpikes = gen(false);
  const maxSpikeSum = Math.max(0, (bot - top) - (CAR_HITBOX_H + 18));
  for (let i = 0; i < count; i++) {
    if (topSpikes[i].h + botSpikes[i].h > maxSpikeSum) {
      if (topSpikes[i].h >= botSpikes[i].h) {
        if (22 + botSpikes[i].h <= maxSpikeSum) { topSpikes[i].h = 22; topSpikes[i].size = 'medium'; }
        else { topSpikes[i].h = 12; topSpikes[i].size = 'small'; }
      } else {
        if (topSpikes[i].h + 22 <= maxSpikeSum) { botSpikes[i].h = 22; botSpikes[i].size = 'medium'; }
        else { botSpikes[i].h = 12; botSpikes[i].size = 'small'; }
      }
    }
  }
  return { topSpikes, botSpikes };
}'''

new_make_spikes = '''function makeSpikes(len, lvl, top, bot, noSpikes = false, levelRng) {
  const count = Math.ceil(len / 12);
  const heights = { small: SPIKE_H_SMALL, medium: SPIKE_H_MEDIUM, big: SPIKE_H_BIG };
  const L = lvl || curLevel;
  const cfg = (typeof getLevelConfig === 'function') ? getLevelConfig(L) : null;
  const stage = getStageNumber(L);
  const allowMixed = (stage >= 3);
  const mixedProbability = (stage === 3) ? 0.20 : 0.35;
  const families = (cfg && cfg.families && cfg.families.length > 0) ? cfg.families : ['classic'];
  const isTwoColor = cfg ? cfg.isTwoColor : false;
  const groupSize = (cfg && cfg.groupSize) ? cfg.groupSize : 4;

  function gen(isTop) {
    const list = [];
    let i = 0;
    while (i < count) {
      const cLen = Math.min(count - i, Math.floor(2 + levelRng() * 4));
      const baseSize = pickClusterSize(L, levelRng);
      const isMixed = allowMixed && (levelRng() < mixedProbability);
      const fam = families[Math.floor(levelRng() * families.length)];

      for (let k = 0; k < cLen; k++) {
        let size = baseSize;
        if (isMixed && k % 2 === 1) {
          size = (baseSize === 'big') ? 'medium' : 'small';
        }
        const h = noSpikes ? 0 : heights[size];
        const spikeFam = fam;
        const colorIdx = isTwoColor ? (Math.floor((i + k) / groupSize) % 2) : 0;
        list.push({ h, size, family: spikeFam, colorIdx });
      }
      i += cLen;
    }
    return list;
  }
  const topSpikes = gen(true);
  const botSpikes = gen(false);
  const maxSpikeSum = Math.max(0, (bot - top) - (CAR_HITBOX_H + 18));
  for (let i = 0; i < count; i++) {
    if (topSpikes[i].h + botSpikes[i].h > maxSpikeSum) {
      if (topSpikes[i].h >= botSpikes[i].h) {
        if (SPIKE_H_MEDIUM + botSpikes[i].h <= maxSpikeSum) { topSpikes[i].h = SPIKE_H_MEDIUM; topSpikes[i].size = 'medium'; }
        else { topSpikes[i].h = SPIKE_H_SMALL; topSpikes[i].size = 'small'; }
      } else {
        if (topSpikes[i].h + SPIKE_H_MEDIUM <= maxSpikeSum) { botSpikes[i].h = SPIKE_H_MEDIUM; botSpikes[i].size = 'medium'; }
        else { botSpikes[i].h = SPIKE_H_SMALL; botSpikes[i].size = 'small'; }
      }
    }
  }
  return { topSpikes, botSpikes };
}'''

if old_make_spikes not in content:
    print('ERROR: old_make_spikes not found!')
    sys.exit(1)
content = content.replace(old_make_spikes, new_make_spikes, 1)

# 2. Replace old renderStageSpike down to prerenderSpikes
start_marker = 'let stageSpikeCanvases = [];\n\nfunction renderStageSpike('
end_marker = 'function drawFluffyClouds(pCtx, x, y, scale = 1, alpha = 0.85, tint = \'#ffffff\') {'

s_pos = content.find(start_marker)
if s_pos == -1:
    print('ERROR: start_marker for renderStageSpike not found!')
    sys.exit(1)

e_pos = content.find(end_marker, s_pos)
if e_pos == -1:
    print('ERROR: end_marker for renderStageSpike not found!')
    sys.exit(1)

render_stage_stud_code = '''function renderStageStud(canvas, isTop, h, family, col) {
  const sCtx = canvas.getContext('2d');
  sCtx.clearRect(0, 0, canvas.width, canvas.height);

  const cx = 27;
  const dir = isTop ? 1 : -1;
  const baseY = isTop ? 6 : 58;
  const tipY = baseY + dir * h;
  const ratio = STUD_RATIOS[family] || 2.4;
  const w = Math.max(6, Math.round(h / ratio));
  const halfW = w / 2;

  // 1. THE BASE COLLAR (about 22 percent of spike height, slightly wider than cone, thin darker ring line at top)
  const collarH = Math.max(2, Math.round(h * 0.22));
  const collarW = Math.max(w + 2, Math.round(w * 1.15));
  const coneBaseY = baseY + dir * collarH;
  const coneH = h - collarH;

  const mainColor = (col && col.main) ? col.main : '#d1d5db';
  const lightColor = (col && col.light) ? col.light : adjustColor(mainColor, 0.40);
  const darkColor = (col && col.dark) ? col.dark : adjustColor(mainColor, -0.45);
  const accentColor = (col && col.accent) ? col.accent : '#ff8a1f';
  const outlineColor = '#0a0d14';

  sCtx.save();

  // Draw Base Collar (cylindrical collar with 3D gradient)
  const collarTop = isTop ? baseY : (baseY - collarH);
  const cGrad = sCtx.createLinearGradient(cx - collarW / 2, 0, cx + collarW / 2, 0);
  cGrad.addColorStop(0.0, lightColor);
  cGrad.addColorStop(0.35, mainColor);
  cGrad.addColorStop(0.70, darkColor);
  cGrad.addColorStop(1.0, adjustColor(darkColor, -0.25));
  sCtx.fillStyle = cGrad;
  sCtx.fillRect(cx - collarW / 2, collarTop, collarW, collarH);

  // Darker ring line at top of collar where cone meets collar
  sCtx.strokeStyle = adjustColor(darkColor, -0.5);
  sCtx.lineWidth = 1;
  sCtx.beginPath();
  sCtx.moveTo(cx - collarW / 2, coneBaseY);
  sCtx.lineTo(cx + collarW / 2, coneBaseY);
  sCtx.stroke();

  // Collar thin outline
  sCtx.strokeStyle = outlineColor;
  sCtx.lineWidth = 0.8;
  sCtx.strokeRect(cx - collarW / 2, collarTop, collarW, collarH);

  // 2. CONE BODY BY FAMILY
  if (family === 'needle') {
    // NEEDLE (ratio 3.6 to 1, thin razor sharp)
    const gL = sCtx.createLinearGradient(cx - halfW, 0, cx, 0);
    gL.addColorStop(0, lightColor);
    gL.addColorStop(1, mainColor);
    sCtx.fillStyle = gL;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.lineTo(cx, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    const gR = sCtx.createLinearGradient(cx, 0, cx + halfW, 0);
    gR.addColorStop(0, mainColor);
    gR.addColorStop(1, darkColor);
    sCtx.fillStyle = gR;
    sCtx.beginPath();
    sCtx.moveTo(cx, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    // Fine highlight stripe
    sCtx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW * 0.45, coneBaseY);
    sCtx.lineTo(cx - 0.5, tipY - dir * 1.5);
    sCtx.stroke();

    // Outline
    sCtx.strokeStyle = outlineColor;
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.stroke();

    // Specular dot
    sCtx.fillStyle = '#ffffff';
    sCtx.beginPath();
    sCtx.arc(cx, tipY - dir * 1, 1, 0, Math.PI * 2);
    sCtx.fill();

  } else if (family === 'fat') {
    // FAT STUD (ratio 1.6 to 1, wide and blunt)
    const tipW = Math.max(2.5, w * 0.22);
    const gBody = sCtx.createLinearGradient(cx - halfW, 0, cx + halfW, 0);
    gBody.addColorStop(0.0, lightColor);
    gBody.addColorStop(0.18, '#ffffff');
    gBody.addColorStop(0.40, mainColor);
    gBody.addColorStop(0.70, darkColor);
    gBody.addColorStop(1.0, adjustColor(darkColor, -0.2));
    sCtx.fillStyle = gBody;

    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx - tipW / 2, tipY);
    sCtx.lineTo(cx + tipW / 2, tipY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    // Broad highlight stripe
    sCtx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
    sCtx.lineWidth = Math.max(1.5, w * 0.18);
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW * 0.5, coneBaseY);
    sCtx.lineTo(cx - tipW * 0.4, tipY - dir * 1.5);
    sCtx.stroke();

    // Outline
    sCtx.strokeStyle = outlineColor;
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx - tipW / 2, tipY);
    sCtx.lineTo(cx + tipW / 2, tipY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.stroke();

    // Blunt cap specular
    sCtx.fillStyle = '#ffffff';
    sCtx.fillRect(cx - tipW * 0.3, tipY - dir * 0.8, tipW * 0.6, 1);

  } else if (family === 'double_cone') {
    // DOUBLE CONE (ratio 2.2 to 1, two stacked cones with a ring between)
    const midY = coneBaseY + dir * (coneH * 0.50);
    const midW = halfW * 0.58;

    // Lower cone
    const gL1 = sCtx.createLinearGradient(cx - halfW, 0, cx + halfW, 0);
    gL1.addColorStop(0.0, lightColor);
    gL1.addColorStop(0.4, mainColor);
    gL1.addColorStop(0.8, darkColor);
    sCtx.fillStyle = gL1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx - midW, midY);
    sCtx.lineTo(cx + midW, midY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    // Divider ring
    const ringH = Math.max(1.5, Math.round(coneH * 0.08));
    sCtx.fillStyle = '#cbd5e1';
    sCtx.fillRect(cx - midW - 1, midY - dir * (ringH / 2), (midW + 1) * 2, ringH);
    sCtx.strokeStyle = outlineColor;
    sCtx.strokeRect(cx - midW - 1, midY - dir * (ringH / 2), (midW + 1) * 2, ringH);

    // Upper cone
    const gL2 = sCtx.createLinearGradient(cx - midW, 0, cx + midW, 0);
    gL2.addColorStop(0.0, lightColor);
    gL2.addColorStop(0.4, mainColor);
    gL2.addColorStop(0.8, darkColor);
    sCtx.fillStyle = gL2;
    sCtx.beginPath();
    sCtx.moveTo(cx - midW, midY);
    sCtx.lineTo(cx, tipY);
    sCtx.lineTo(cx + midW, midY);
    sCtx.closePath();
    sCtx.fill();

    // Outlines & highlights
    sCtx.strokeStyle = outlineColor;
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx - midW, midY);
    sCtx.lineTo(cx, tipY);
    sCtx.lineTo(cx + midW, midY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.stroke();

    sCtx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
    sCtx.lineWidth = 1.2;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW * 0.5, coneBaseY);
    sCtx.lineTo(cx - 0.6, tipY - dir * 1.5);
    sCtx.stroke();

    sCtx.fillStyle = '#ffffff';
    sCtx.beginPath();
    sCtx.arc(cx, tipY - dir * 1.2, 1.1, 0, Math.PI * 2);
    sCtx.fill();

  } else if (family === 'crystal') {
    // FACETED CRYSTAL (ratio 2.3 to 1, 4 visible facets with distinct brightness)
    const f1 = adjustColor(lightColor, 0.40);
    const f2 = lightColor;
    const f3 = mainColor;
    const f4 = darkColor;

    // Facet 1 (far left)
    sCtx.fillStyle = f1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx - halfW * 0.35, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.closePath();
    sCtx.fill();

    // Facet 2 (mid left)
    sCtx.fillStyle = f2;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW * 0.35, coneBaseY);
    sCtx.lineTo(cx, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.closePath();
    sCtx.fill();

    // Facet 3 (mid right)
    sCtx.fillStyle = f3;
    sCtx.beginPath();
    sCtx.moveTo(cx, coneBaseY);
    sCtx.lineTo(cx + halfW * 0.45, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.closePath();
    sCtx.fill();

    // Facet 4 (far right)
    sCtx.fillStyle = f4;
    sCtx.beginPath();
    sCtx.moveTo(cx + halfW * 0.45, coneBaseY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.closePath();
    sCtx.fill();

    // Facet edge lines
    sCtx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
    sCtx.lineWidth = 0.8;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW * 0.35, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.moveTo(cx, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.stroke();

    // Outline
    sCtx.strokeStyle = outlineColor;
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.stroke();

    // Specular dot
    sCtx.fillStyle = '#ffffff';
    sCtx.beginPath();
    sCtx.arc(cx, tipY - dir * 1.2, 1.2, 0, Math.PI * 2);
    sCtx.fill();

  } else if (family === 'curved_thorn') {
    // CURVED THORN (ratio 2.5 to 1, tip bends to one side by 25 percent width)
    const bend = w * 0.25;
    const tipX = cx + bend;

    const gThorn = sCtx.createLinearGradient(cx - halfW, 0, cx + halfW + bend, 0);
    gThorn.addColorStop(0.0, lightColor);
    gThorn.addColorStop(0.25, '#ffffff');
    gThorn.addColorStop(0.50, mainColor);
    gThorn.addColorStop(0.85, darkColor);
    sCtx.fillStyle = gThorn;

    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.quadraticCurveTo(cx - halfW * 0.2 + bend * 0.4, coneBaseY + dir * coneH * 0.6, tipX, tipY);
    sCtx.quadraticCurveTo(cx + halfW * 0.3 + bend * 0.4, coneBaseY + dir * coneH * 0.6, cx + halfW, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    // Curved highlight
    sCtx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
    sCtx.lineWidth = 1.2;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW * 0.4, coneBaseY);
    sCtx.quadraticCurveTo(cx - halfW * 0.1 + bend * 0.4, coneBaseY + dir * coneH * 0.6, tipX - 0.5, tipY - dir * 1.5);
    sCtx.stroke();

    // Outline
    sCtx.strokeStyle = outlineColor;
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.quadraticCurveTo(cx - halfW * 0.2 + bend * 0.4, coneBaseY + dir * coneH * 0.6, tipX, tipY);
    sCtx.quadraticCurveTo(cx + halfW * 0.3 + bend * 0.4, coneBaseY + dir * coneH * 0.6, cx + halfW, coneBaseY);
    sCtx.stroke();

    sCtx.fillStyle = '#ffffff';
    sCtx.beginPath();
    sCtx.arc(tipX, tipY - dir * 1, 1.1, 0, Math.PI * 2);
    sCtx.fill();

  } else if (family === 'mace') {
    // MACE STUD (ratio 2.2 to 1, cone ending in a small ball)
    const ballR = Math.max(2.4, w * 0.26);
    const ballY = tipY - dir * ballR;

    // Cone stem
    const gStem = sCtx.createLinearGradient(cx - halfW, 0, cx + halfW, 0);
    gStem.addColorStop(0.0, lightColor);
    gStem.addColorStop(0.45, mainColor);
    gStem.addColorStop(0.85, darkColor);
    sCtx.fillStyle = gStem;

    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx - ballR * 0.7, ballY);
    sCtx.lineTo(cx + ballR * 0.7, ballY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    // Mace Ball with 3D radial sphere gradient
    const bGrad = sCtx.createRadialGradient(cx - ballR * 0.35, ballY - dir * ballR * 0.35, 0.5, cx, ballY, ballR);
    bGrad.addColorStop(0.0, '#ffffff');
    bGrad.addColorStop(0.3, lightColor);
    bGrad.addColorStop(0.7, mainColor);
    bGrad.addColorStop(1.0, darkColor);
    sCtx.fillStyle = bGrad;
    sCtx.beginPath();
    sCtx.arc(cx, ballY, ballR, 0, Math.PI * 2);
    sCtx.fill();

    // Small metallic studs on mace ball
    sCtx.fillStyle = '#ffffff';
    sCtx.beginPath();
    sCtx.arc(cx, ballY + dir * ballR, 0.8, 0, Math.PI * 2);
    sCtx.arc(cx - ballR, ballY, 0.8, 0, Math.PI * 2);
    sCtx.arc(cx + ballR, ballY, 0.8, 0, Math.PI * 2);
    sCtx.fill();

    // Outlines
    sCtx.strokeStyle = outlineColor;
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx - ballR * 0.7, ballY);
    sCtx.stroke();
    sCtx.beginPath();
    sCtx.moveTo(cx + halfW, coneBaseY);
    sCtx.lineTo(cx + ballR * 0.7, ballY);
    sCtx.stroke();
    sCtx.beginPath();
    sCtx.arc(cx, ballY, ballR, 0, Math.PI * 2);
    sCtx.stroke();

  } else if (family === 'bullet') {
    // BULLET STUD (ratio 2.1 to 1, round tip, very glossy)
    const midH = coneH * 0.45;
    const midY = coneBaseY + dir * midH;
    const domeR = halfW;

    // Cylindrical lower section + rounded dome
    const gBul = sCtx.createLinearGradient(cx - halfW, 0, cx + halfW, 0);
    gBul.addColorStop(0.0, lightColor);
    gBul.addColorStop(0.18, '#ffffff');
    gBul.addColorStop(0.40, mainColor);
    gBul.addColorStop(0.70, darkColor);
    gBul.addColorStop(1.0, adjustColor(darkColor, -0.3));
    sCtx.fillStyle = gBul;

    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx - halfW, midY);
    sCtx.arc(cx, midY, domeR, Math.PI, 0, isTop ? false : true);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    // Super glossy highlight curve
    sCtx.strokeStyle = 'rgba(255, 255, 255, 0.95)';
    sCtx.lineWidth = Math.max(1.2, w * 0.18);
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW * 0.5, coneBaseY);
    sCtx.lineTo(cx - halfW * 0.5, midY);
    sCtx.quadraticCurveTo(cx - halfW * 0.4, tipY, cx - 1, tipY - dir * 1.5);
    sCtx.stroke();

    // Outline
    sCtx.strokeStyle = outlineColor;
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx - halfW, midY);
    sCtx.arc(cx, midY, domeR, Math.PI, 0, isTop ? false : true);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.stroke();

  } else if (family === 'flame') {
    // FLAME STUD (ratio 2.4 to 1, orange-red gradient cone with flame lick tip)
    const gFlame = sCtx.createLinearGradient(0, coneBaseY, 0, tipY);
    gFlame.addColorStop(0.0, '#b91c1c'); // Crimson red base
    gFlame.addColorStop(0.5, '#f97316'); // Vibrant orange
    gFlame.addColorStop(1.0, '#fef08a'); // Lick of yellow fire at tip
    sCtx.fillStyle = gFlame;

    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.quadraticCurveTo(cx - halfW * 0.1, coneBaseY + dir * coneH * 0.6, cx + 1, tipY);
    sCtx.quadraticCurveTo(cx + halfW * 0.2, coneBaseY + dir * coneH * 0.6, cx + halfW, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    // Inner bright flame core
    sCtx.fillStyle = 'rgba(254, 240, 138, 0.85)';
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW * 0.35, coneBaseY + dir * 2);
    sCtx.lineTo(cx, tipY - dir * 1.5);
    sCtx.lineTo(cx + halfW * 0.2, coneBaseY + dir * 2);
    sCtx.closePath();
    sCtx.fill();

    // Outline
    sCtx.strokeStyle = '#450a0a';
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.quadraticCurveTo(cx - halfW * 0.1, coneBaseY + dir * coneH * 0.6, cx + 1, tipY);
    sCtx.quadraticCurveTo(cx + halfW * 0.2, coneBaseY + dir * coneH * 0.6, cx + halfW, coneBaseY);
    sCtx.stroke();

  } else {
    // CLASSIC (ratio 2.4 to 1, smooth cone bullet stud with 3D highlight)
    const gL = sCtx.createLinearGradient(cx - halfW, 0, cx, 0);
    gL.addColorStop(0, lightColor);
    gL.addColorStop(1, mainColor);
    sCtx.fillStyle = gL;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.lineTo(cx, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    const gR = sCtx.createLinearGradient(cx, 0, cx + halfW, 0);
    gR.addColorStop(0, mainColor);
    gR.addColorStop(1, darkColor);
    sCtx.fillStyle = gR;
    sCtx.beginPath();
    sCtx.moveTo(cx, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.closePath();
    sCtx.fill();

    // Bright white highlight stripe on left (~18% of width)
    sCtx.strokeStyle = 'rgba(255, 255, 255, 0.92)';
    sCtx.lineWidth = Math.max(1.1, w * 0.18);
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW * 0.45, coneBaseY);
    sCtx.lineTo(cx - 0.7, tipY - dir * 1.8);
    sCtx.stroke();

    // Exact cone outline
    sCtx.strokeStyle = outlineColor;
    sCtx.lineWidth = 1;
    sCtx.beginPath();
    sCtx.moveTo(cx - halfW, coneBaseY);
    sCtx.lineTo(cx, tipY);
    sCtx.lineTo(cx + halfW, coneBaseY);
    sCtx.stroke();

    // White specular glint at tip
    sCtx.fillStyle = '#ffffff';
    sCtx.beginPath();
    sCtx.arc(cx - 0.4, tipY - dir * 1.2, 1.2, 0, Math.PI * 2);
    sCtx.fill();
  }

  sCtx.restore();
}
\n'''

content = content[:s_pos] + render_stage_stud_code + content[e_pos:]

# 3. Replace prerenderAllStageSpikes and prerenderSpikes
old_prerender = '''// Pre-render spike sprites once per stage and reuse them (Requirement 4 & 5)
function prerenderAllStageSpikes() {
  stageSpikeCanvases.length = 0;
  const sizes = { small: 12, medium: 22, big: 36 };

  for (let sIdx = 0; sIdx < STAGES.length; sIdx++) {
    const stage = STAGES[sIdx];
    const stageMap = {};
    const hasVariants = (sIdx === 4 || sIdx === 5);
    const variants = hasVariants ? [0, 1] : [0];

    for (const sKey in sizes) {
      const h = sizes[sKey];
      for (const dir of ['top', 'bot']) {
        for (const v of variants) {
          const key = hasVariants ? `${sKey}_${dir}_${v}` : `${sKey}_${dir}`;
          const canvas = document.createElement('canvas');
          canvas.width = 40;
          canvas.height = 52;
          renderStageSpike(canvas, dir === 'top', h, stage, v);
          stageMap[key] = canvas;
          if (hasVariants && v === 0) {
            stageMap[`${sKey}_${dir}`] = canvas;
          }
        }
      }
    }
    stageSpikeCanvases.push(stageMap);
  }
}

function prerenderSpikes(cfg) {
  if (!stageSpikeCanvases || stageSpikeCanvases.length === 0) {
    prerenderAllStageSpikes();
  }
  const stageIdx = (getStageNumber(curLevel) - 1) % STAGES.length;
  spikeCanvases = stageSpikeCanvases[stageIdx] || {};
}'''

new_prerender = '''function prerenderSpikes(cfg) {
  spikeCanvases = {};
  if (!cfg) return;

  const families = (cfg.families && cfg.families.length > 0) ? cfg.families : ['classic'];
  const colors = (cfg.colors && cfg.colors.length > 0) ? cfg.colors : [{
    main: '#d1d5db', light: '#f1f5f9', dark: '#64748b', accent: '#ff8a1f', glow: '#ff8a1f'
  }];
  const sizes = { small: SPIKE_H_SMALL, medium: SPIKE_H_MEDIUM, big: SPIKE_H_BIG };

  for (const fam of families) {
    for (let cIdx = 0; cIdx < colors.length; cIdx++) {
      const col = colors[cIdx];
      for (const sKey in sizes) {
        const h = sizes[sKey];
        for (const dir of ['top', 'bot']) {
          const canvas = document.createElement('canvas');
          canvas.width = 54;
          canvas.height = 64;
          renderStageStud(canvas, dir === 'top', h, fam, col);
          const key = `${fam}_${cIdx}_${dir}_${sKey}`;
          spikeCanvases[key] = canvas;
          if (cIdx === 0 && fam === families[0]) {
            spikeCanvases[`${sKey}_${dir}`] = canvas;
          }
        }
      }
    }
  }
}'''

if old_prerender not in content:
    print('ERROR: old_prerender not found!')
    sys.exit(1)
content = content.replace(old_prerender, new_prerender, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('SUCCESS: renderStageStud and prerenderSpikes updated!')
