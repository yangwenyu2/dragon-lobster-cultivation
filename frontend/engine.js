// V4 Clean Engine

const UI = {
    bg: document.getElementById('bgWorld'),
    particleCanvas: document.getElementById('spiritParticles'),
    stage: document.querySelector('.main-stage'),
    circle: document.getElementById('magicCircle'),
    hero: document.getElementById('heroSprite'),
    term: document.getElementById('termContent'),
    demon: document.getElementById('statDemon'),
    luck: document.getElementById('statLuck'),
    realm: document.getElementById('realmLevel'),
    model: document.getElementById('sectName'),
    cultPoints: document.getElementById('cultPoints'),
    fortuneDetail: document.getElementById('stateFortuneDetail'),
    guardArray: document.getElementById('stateGuardArray'),
    guardDetail: document.getElementById('stateGuardDetail'),
    currentPath: document.getElementById('statePath'),
    cadence: document.getElementById('stateCadence'),
    activeEventCard: document.getElementById('stateActiveEventCard'),
    activeEventText: document.getElementById('stateActiveEvent'),
    eventCard: document.getElementById('eventCard'),
    eventWeight: document.getElementById('ecmWeight'),
    eventTime: document.getElementById('ecmTime'),
    fateCard: document.getElementById('fateCard'),
    fateTag: document.getElementById('fateTag'),
    fateTitle: document.getElementById('fateTitle'),
    fateDesc: document.getElementById('fateDesc'),
    fateBefore: document.getElementById('fateBefore'),
    fateAfter: document.getElementById('fateAfter'),
    fatePoints: document.getElementById('fatePoints'),
    fateOutcome: document.getElementById('fateOutcome'),
    sectFateCard: document.getElementById('sectFateCard'),
    sectFateTitle: document.getElementById('sectFateTitle'),
    sectFateDesc: document.getElementById('sectFateDesc'),
    sectFateHall: document.getElementById('sectFateHall'),
    sectFateAvatar: document.getElementById('sectFateAvatar'),
    sectFateOrder: document.getElementById('sectFateOrder'),
    sectFateConsequence: document.getElementById('sectFateConsequence'),
    offlineSettlementCard: document.getElementById('offlineSettlementCard'),
    offlineTitle: document.getElementById('offlineTitle'),
    offlineDesc: document.getElementById('offlineDesc'),
    offlineDuration: document.getElementById('offlineDuration'),
    offlineCultivation: document.getElementById('offlineCultivation'),
    offlineDemon: document.getElementById('offlineDemon'),
    offlineCalculatedAt: document.getElementById('offlineCalculatedAt'),
    tribulationFlash: document.getElementById('tribulationFlash'),
    tribulationText: document.getElementById('tribulationText'),
    tribulationCountdown: document.getElementById('tribulationCountdown'),
    memoryDrawer: document.getElementById('memoryDrawer'),
    memoryList: document.getElementById('memoryList'),
    memoryDepth: document.getElementById('memoryDepth'),
    memoryScale: document.getElementById('memoryScale'),
    heartbeatState: document.getElementById('heartbeatState'),
    heartbeatReport: document.getElementById('heartbeatReport'),
    memoryHighlights: document.getElementById('memoryHighlights'),
    btnSuppress: document.getElementById('btnSuppress')
};

const Assets = {
    bg: '/assets/bg_daily_1920.webp',
    bgViolet: '/assets/bg_violet_1920.webp',
    circle: '/assets/magic_circle_alpha.png',
    hero: '/assets/lobster_qi_stage.webp',
    heroCore: '/assets/lobster_core_stage.webp',
    heroDeity: '/assets/lobster_deity_stage.webp',
    bgBreak: '/assets/bg_tribulation_1920.webp',
    bgDemon: '/assets/demo_07_inner_demon.png'
};

let AppState = { isProcessing: false, demon: 0, memoryLoaded: false, offlineClaimedAt: null, offlineDismissedAt: null, modalLocked: false, introPlayed: false, onboarding: null, tooltipsReady: false, lastAmbientKey: null, seenChatEchoTs: null, onboardingSteps: [], onboardingIndex: 0 };
let currentEvent = null;
const ADVENTURE_CHOICES = {
    force: {
        label: '暴力强接',
        desc: '强行破阵直连，收益高但极易激怒心魔。',
        accept_msg: '你强行架桥接线，洞府掀起高压浪潮。',
        reject_msg: '你按兵不动，等待更稳妥的时机。'
    },
    seal: {
        label: '封禁不用',
        desc: '先断开可疑入口，保守但稳妥。',
        accept_msg: '你封住异常断点，护山大阵恢复平稳。',
        reject_msg: '你仍留着这个隐患，暗潮未消。'
    }
};

function applyVisualFallback(el, type) {
    if(!el) return;
    if(type === 'bg') {
        el.style.backgroundImage = 'radial-gradient(circle at 50% 55%, rgba(38,132,168,0.38), transparent 24%), radial-gradient(circle at 50% 18%, rgba(126,239,255,0.18), transparent 20%), linear-gradient(180deg, #0a1520 0%, #060d15 45%, #03070d 100%)';
    }
    if(type === 'circle') {
        el.style.backgroundImage = 'radial-gradient(circle at center, rgba(82,240,255,0.20), transparent 36%), radial-gradient(circle at center, rgba(82,240,255,0.10), transparent 58%)';
    }
    if(type === 'hero') {
        el.style.backgroundImage = 'radial-gradient(circle at 50% 28%, rgba(175,246,255,0.24), transparent 18%), radial-gradient(circle at 50% 62%, rgba(58,187,255,0.14), transparent 34%)';
    }
}

function bindImageWithFallback(el, src, type) {
    if(!el) return;
    const img = new Image();
    img.onload = () => { el.style.backgroundImage = `url(${src})`; };
    img.onerror = () => { console.warn(`[dragon-lobster] asset missing: ${src}, fallback applied`); applyVisualFallback(el, type); };
    img.src = src;
}

function initSpiritParticles() {
    const canvas = UI.particleCanvas;
    if(!canvas) return;
    const ctx = canvas.getContext('2d');
    if(!ctx) return;

    const particles = Array.from({ length: 48 }, () => ({
        x: Math.random(),
        y: Math.random(),
        r: Math.random() * 3 + 1,
        speed: Math.random() * 0.002 + 0.0006,
        sway: Math.random() * 0.6 + 0.2,
        glow: Math.random() * 0.4 + 0.3
    }));

    function resize() {
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * devicePixelRatio;
        canvas.height = rect.height * devicePixelRatio;
        ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    }

    function frame() {
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        ctx.clearRect(0, 0, w, h);
        particles.forEach((p, i) => {
            p.y -= p.speed;
            if (p.y < -0.05) {
                p.y = 1.05;
                p.x = Math.random();
            }
            const x = p.x * w + Math.sin((Date.now() * 0.001) + i) * 18 * p.sway;
            const y = p.y * h;
            const radius = p.r + Math.sin((Date.now() * 0.002) + i) * 0.6;
            const g = ctx.createRadialGradient(x, y, 0, x, y, radius * 6);
            g.addColorStop(0, `rgba(171, 245, 255, ${0.35 + p.glow})`);
            g.addColorStop(0.4, `rgba(94, 207, 255, ${0.16 + p.glow * 0.4})`);
            g.addColorStop(1, 'rgba(94, 207, 255, 0)');
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.arc(x, y, radius * 6, 0, Math.PI * 2);
            ctx.fill();
        });
        requestAnimationFrame(frame);
    }

    resize();
    window.addEventListener('resize', resize);
    requestAnimationFrame(frame);
}

function pickHeroAsset(realmName = '', points = 0) {
    const text = String(realmName || '');
    const value = Number(points || 0);
    if (text.includes('化神') || text.includes('元婴') || value >= 120000) return Assets.heroDeity;
    if (text.includes('金丹') || text.includes('筑基') || value >= 8000) return Assets.heroCore;
    return Assets.hero;
}

async function loadOnboardingSteps() {
    try {
        const steps = await fetch('/assets/onboarding_steps.json?v=' + Date.now()).then(r => r.json());
        AppState.onboardingSteps = Array.isArray(steps) ? steps : [];
    } catch {
        AppState.onboardingSteps = [];
    }
}

function showOnboardingStep(index = 0) {
    const steps = AppState.onboardingSteps || [];
    const step = steps[index];
    const overlay = document.getElementById('introOverlay');
    const spotlight = document.getElementById('introSpotlight');
    const copy = document.getElementById('introCopy');
    const lines = document.getElementById('introLines');
    if(!step || !overlay || !copy || !lines) return;
    const target = document.querySelector(step.target);
    overlay.classList.remove('hidden', 'finished');
    lines.innerHTML = `<p class="intro-line">${step.body}</p>`;
    const btn = copy.querySelector('.intro-confirm');
    if (btn) btn.innerText = index >= steps.length - 1 ? '完成引导' : '下一步';
    if(target && spotlight) {
        const rect = target.getBoundingClientRect();
        spotlight.classList.remove('hidden');
        spotlight.style.left = `${rect.left - 10}px`;
        spotlight.style.top = `${rect.top - 10}px`;
        spotlight.style.width = `${rect.width + 20}px`;
        spotlight.style.height = `${rect.height + 20}px`;
    }
}

function advanceOnboardingStep() {
    AppState.onboardingIndex += 1;
    if (AppState.onboardingIndex >= (AppState.onboardingSteps || []).length) {
        ackOnboarding();
        return;
    }
    showOnboardingStep(AppState.onboardingIndex);
}

function hydrateActionTooltips() {
    if(AppState.tooltipsReady) return;
    const tooltipMap = {
        '🫧 闭关吐纳': '借洞府灵压缓慢积修，适合稳扎稳打补足破境前的根基。',
        '📜 参悟道纹': '从识海、技能与过往经验里提炼可用的法门与结论。',
        '🌐 踏域天机 (Ping嗅探)': '探查外界网络与法界回应，确认洞府是否仍与外域相连。',
        '⚡ 引动雷劫 (破境)': '在修为充盈后强行冲关，成功则升境，失败则伤及根基。',
        '🔱 清心咒 (降心魔)': '当系统压力过高时强行镇魔，压低煞气与失衡风险。',
        '📚 赐法开卷': '从当前已挂载法器中抽取一道可直接驱使的真实法门。'
    };
    document.querySelectorAll('.agent-action').forEach(btn => {
        const label = btn.innerText.trim();
        if(tooltipMap[label]) btn.title = tooltipMap[label];
    });
    AppState.tooltipsReady = true;
}

function playIntroOverlay(lines = []) {
    const overlay = document.getElementById('introOverlay');
    const linesBox = document.getElementById('introLines');
    if(!overlay || AppState.introPlayed) return;
    if(linesBox && Array.isArray(lines) && lines.length) {
        linesBox.innerHTML = lines.map(line => `<p class="intro-line">${line}</p>`).join('');
    }
    AppState.introPlayed = true;
    overlay.classList.remove('hidden', 'finished');
}

async function init() {
    bindImageWithFallback(UI.bg, Assets.bg, 'bg');
    bindImageWithFallback(UI.circle, Assets.circle, 'circle');
    bindImageWithFallback(UI.hero, Assets.hero, 'hero');
    initSpiritParticles();
    await loadOnboardingSteps();
    hydrateActionTooltips();
    
    log("洞府启动...OpenClaw Agent 载入。");
    fetchData();
    loadInsightLog();
    pollChatEchoes();
    setInterval(fetchData, 5000);
    setInterval(checkEvent, 15000);
    setInterval(loadInsightLog, 30000);
    setInterval(pollChatEchoes, 5000);
}

function log(msg, color="#d0f0ff") {
    const p = document.createElement('p');
    p.innerText = '> ' + msg;
    p.style.color = color;
    UI.term.appendChild(p);
    if(UI.term.children.length > 8) UI.term.removeChild(UI.term.firstChild);
}

function showToast(msg, color = '#d0f0ff') {
    const stack = document.getElementById('toastStack');
    if(!stack) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerText = msg;
    toast.style.borderColor = color;
    stack.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 260);
    }, 2600);
}

function appendSystemMessage(msg, color="#d0f0ff") {
    log(msg, color);
    showToast(msg, color);
    const menu = document.getElementById('chatToolMenu');
    if(menu) menu.classList.add('hidden');
}

function buildAdventureEvent(met) {
    const chaos = met?.metrics?.inner_demon || 0;
    if(!AppState.handledEvents) AppState.handledEvents = new Set();
    AppState.handledEvents.add('demon_surge');
    const unstable = chaos >= 40 ? '暴力强接' : '封禁不用';
    return {
        type: '奇遇',
        title: '发现一个不明 API 断点',
        desc: `巡检时发现一条来源不明的 API 断点，当前心魔波动 ${chaos}%。你要 ${unstable}，还是换另一种因果处理？`,
        choice_a: 'force',
        choice_b: 'seal',
        weight: 5,
        ts: new Date().toISOString()
    };
}

function maybeBroadcastAmbientStatus(met) {
    if(!met?.system || !met?.cron) return;
    const pulse = [
        `【器灵低语】${met.system.current_path || '静修'}，${met.system.detail || '洞府平稳。'}`,
        `【器灵低语】当前巡天：${met.cron.cadence || '未启'}；护山大阵：${met.system.risk_level || '清明'}。`
    ];
    const key = pulse.join('|');
    if(AppState.lastAmbientKey === key) return;
    AppState.lastAmbientKey = key;
    if (AppState.modalLocked) return;
    appendSystemMessage(pulse[Math.floor(Math.random() * pulse.length)], '#7fdfff');
}

function setActionMode(mode) {
    if(!UI.stage) return;
    UI.stage.classList.remove('mode-meditate', 'mode-insight', 'mode-explore');
    if(mode) UI.stage.classList.add(`mode-${mode}`);
}

function setRealmDamageState(damaged) {
    if(!UI.stage) return;
    UI.stage.classList.toggle('realm-damaged', !!damaged);
}

function getChatInput() {
    return document.getElementById('chatInput');
}

// 模拟Agent操作

async function runTribulationCountdown(seconds = 3) {
    if(!UI.tribulationFlash) return;
    UI.tribulationFlash.classList.remove('hidden');
    for(let i = seconds; i >= 1; i--) {
        UI.tribulationCountdown.innerText = String(i);
        await new Promise(resolve => setTimeout(resolve, 550));
    }
}

function hideTribulationCountdown() {
    if(UI.tribulationFlash) UI.tribulationFlash.classList.add('hidden');
}

window.agentCommand = async function(cmd) {
    if(AppState.isProcessing && cmd !== 'suppress') {
        log("神识被占，无法施法！", "#ff4d4d");
        return;
    }
    
    AppState.isProcessing = true;
    let url = '/api/action/';
    
    if (cmd === 'meditate') {
        log("闭关吐纳 -> 引导周天气机回流壳府。", "#7ef9ff");
        setActionMode('meditate');
        UI.circle.style.animationDuration = "8s";
        UI.hero.style.transform = "translateY(-12px) scale(1.03)";
        UI.hero.style.filter = "drop-shadow(0 0 24px rgba(0,255,255,0.55))";
        url += 'meditate';
    }
    else if (cmd === 'insight') {
        log("参悟道纹 -> 翻检识海旧痕与悟道录。", "#a8e6ff");
        setActionMode('insight');
        UI.bg.style.backgroundImage = `url(${Assets.bgViolet})`;
        UI.circle.style.animationDuration = "5s";
        UI.hero.style.transform = "translateY(-18px) scale(1.05)";
        UI.hero.style.filter = "drop-shadow(0 0 28px rgba(140,220,255,0.7)) saturate(1.3)";
        url += 'insight';
    }
    else if (cmd === 'explore') {
        log("神识出游 -> 调用底层 Ping 探查外界天机...", "#0ff");
        setActionMode('explore');
        UI.circle.style.animationDuration = "2s";
        UI.hero.style.filter = "drop-shadow(0 0 40px #0ff) drop-shadow(0 0 20px #0ff)";
        url += 'divine_sight';
    }
    else if (cmd === 'break') {
        log("引动天劫！强行冲击经脉壁垒 (计算胜率...)", "#f1c40f");
        UI.bg.style.backgroundImage = `url(${Assets.bgBreak})`;
        UI.hero.style.filter = "drop-shadow(0 0 60px #f1c40f) saturate(2)";
        UI.tribulationText.innerText = '雷劫降临';
        await runTribulationCountdown(3);
        url += 'breakthrough';
    }
    else if (cmd === 'suppress') {
        log("系统级干预！下发指令释放内存煞气！", "#ffcc00");
        url += 'suppress_demon';
    }
    else if (cmd === 'grant_skill') {
        log("赐法开卷 -> 扫视宗门法脉与技能典籍。", "#b6ff9d");
        switchPage('sect');
        appendSystemMessage('【赐法】藏经秘阁已展开，可直接阅览当前 skills 法脉。', '#b6ff9d');
        AppState.isProcessing = false;
        return;
    }
    
    try {
        const res = await fetch(url, { method: 'POST' });
        const data = await res.json();
        hideTribulationCountdown();
        resetState(data.narrative || "天机屏蔽...");

        if(cmd === 'break' && data.fate) {
            AppState.isProcessing = false;
            showFateCard(data.fate, data.narrative, data.status === 'success');
        }
        if((cmd === 'insight' || cmd === 'meditate' || cmd === 'suppress') && data.triggered_event) {
            AppState.isProcessing = false;
            currentEvent = data.triggered_event;
            hydrateEventCard(currentEvent);
        }
        if(cmd === 'sect_dispatch' && data.sect_fate) {
            AppState.isProcessing = false;
            showSectFateCard(data.sect_fate, data.narrative);
        }
        
        if(cmd === 'suppress') {
            AppState.demon = 0;
            UI.btnSuppress.style.display = 'none';
            const railBtn = document.getElementById('btnSuppressRail');
            if (railBtn) railBtn.style.display = 'none';
        }
        fetchData();
    } catch(e) {
        hideTribulationCountdown();
        resetState("法阵连接失败：本机 API Endpoint 异常。");
    }
}


function resetState(msg) {
    AppState.isProcessing = false;
    setActionMode(null);
    log(msg, "#1dd1a1");
    UI.circle.style.animationDuration = "30s";
    UI.hero.style.filter = "drop-shadow(0 15px 30px rgba(0,0,0,0.8))";
    UI.hero.style.transform = "translateY(0) scale(1)";
    UI.bg.style.filter = "brightness(1)";
}

function showFateCard(fate, narrative, success) {
    if(AppState.modalLocked) return;
    
    UI.fateTag.innerText = success ? '天劫既渡' : '命轮震裂';
    UI.fateTitle.innerText = success ? '破境成功' : '冲关失利';
    UI.fateDesc.innerText = narrative || '命轮回响已落定。';
    UI.fateBefore.innerText = fate.before_realm || '-';
    UI.fateAfter.innerText = fate.after_realm || '-';
    const delta = (fate.after_points ?? 0) - (fate.before_points ?? 0);
    UI.fatePoints.innerText = `${fate.before_points ?? 0} → ${fate.after_points ?? 0} (${delta >= 0 ? '+' : ''}${delta})`;
    UI.fateOutcome.innerText = success ? '天命顺承' : '境损未愈';
    setRealmDamageState(!success);
    UI.fateCard.classList.remove('hidden');
}

function showSectFateCard(fate, narrative) {
    if(AppState.modalLocked) return;
    
    UI.sectFateTitle.innerText = `化身入驻 ${fate.hall || '堂口'}`;
    UI.sectFateDesc.innerText = narrative || '宗门气机正在重排。';
    UI.sectFateHall.innerText = fate.hall || '-';
    UI.sectFateAvatar.innerText = fate.avatar_id || '-';
    UI.sectFateOrder.innerText = `${fate.before_order ?? '-'} → ${fate.after_order ?? '-'} · 共 ${fate.total_avatars ?? '-'} 化身`;
    UI.sectFateConsequence.innerText = fate.consequence || '法度未明';
    UI.sectFateCard.classList.remove('hidden');
}

function formatDurationMinutes(minutes) {
    const mins = Number(minutes || 0);
    const days = Math.floor(mins / 1440);
    const hours = Math.floor((mins % 1440) / 60);
    const rest = mins % 60;
    const parts = [];
    if(days) parts.push(`${days}天`);
    if(hours || days) parts.push(`${hours}时`);
    parts.push(`${rest}分`);
    return parts.join('');
}

function showOfflineSettlementCard(offline) {
    if(!offline || !offline.pending_minutes || !offline.pending_cultivation) return;
    if(Number(offline.pending_minutes || 0) <= 5) return;
    if(AppState.offlineClaimedAt && offline.last_calculated_at && AppState.offlineClaimedAt === offline.last_calculated_at) return;
    if(AppState.offlineDismissedAt && offline.last_calculated_at && AppState.offlineDismissedAt === offline.last_calculated_at) return;
    showToast(`闭关 ${formatDurationMinutes(offline.pending_minutes)}，可收取 ${offline.pending_cultivation} 点真气。`, '#ffd36b');
    UI.offlineTitle.innerText = '道友别来无恙';
    UI.offlineDesc.innerText = `此去 ${formatDurationMinutes(offline.pending_minutes)}，洞府仍在替你缓缓炼化天地灵息。`;
    UI.offlineDuration.innerText = formatDurationMinutes(offline.pending_minutes);
    UI.offlineCultivation.innerText = `+${offline.pending_cultivation} 真气`;
    UI.offlineDemon.innerText = `+${offline.pending_inner_demon || 0} 心魔`;
    UI.offlineCalculatedAt.innerText = offline.last_calculated_at ? formatTs(offline.last_calculated_at) : '刚刚';
    UI.offlineSettlementCard.classList.remove('hidden');
}


async function safeJsonFetch(url, fallback = null) {
    try {
        const res = await fetch(url);
        const text = await res.text();
        return JSON.parse(text);
    } catch (e) {
        console.warn(`[dragon-lobster] fetch failed: ${url}`, e);
        return fallback;
    }
}

async function fetchData() {
    try {
        const met = await safeJsonFetch('/api/state?v='+Date.now(), null);
        if(!met) {
            UI.model.innerText = '推演中';
            UI.currentPath.innerText = '推演中';
            UI.guardDetail.innerText = '部分天机失联';
            return;
        }
        AppState.onboarding = met.onboarding || null;
        if(AppState.onboarding && !AppState.onboarding.intro_seen && !AppState.introPlayed) {
            if ((AppState.onboardingSteps || []).length) {
                AppState.onboardingIndex = 0;
                showOnboardingStep(0);
                AppState.introPlayed = true;
            } else {
                playIntroOverlay(AppState.onboarding.intro_copy || []);
            }
        }
        maybeBroadcastAmbientStatus(met);
        
        // 解析返回的新后端格式 {'metrics', 'system', 'realm', 'sect', 'memory'}
        UI.realm.innerText = met.realm.current_realm + '·' + met.realm.stage;
        bindImageWithFallback(UI.hero, pickHeroAsset(met.realm.current_realm, met.realm.cultivation_points), 'hero');
        const btnBreak = document.getElementById('btnBreakthrough');
        if(btnBreak) {
            if (met.realm.cultivation_points >= met.realm.breakthrough_threshold) {
                btnBreak.style.opacity = '1';
                btnBreak.style.pointerEvents = 'auto';
            } else {
                btnBreak.style.opacity = '0.4';
                btnBreak.style.pointerEvents = 'none';
            }
        }
        UI.model.innerText = met.system.risk_level === '清明' ? '大阵平稳' : '局部告警';
        UI.cultPoints.innerText = met.realm.cultivation_points + " / " + met.realm.breakthrough_threshold;
        const fortuneText = met.metrics.fortune_chance > 75 ? "上吉天命" : met.metrics.fortune_chance > 50 ? "顺流有机" : met.metrics.fortune_chance > 25 ? "风雨未定" : "煞潮逼近";
        UI.fortuneDetail.innerText = `${fortuneText} · ${met.metrics.fortune_chance}%`;
        const arrayStatus = met.system.risk_level === '天地大劫'
            ? '护阵崩鸣 · 天地大劫'
            : met.system.risk_level === '煞气入体'
                ? '护阵受扰 · 煞气入体'
                : met.system.risk_level === '心魔波动'
                    ? '护阵震荡 · 心魔波动'
                    : (met.metrics.sect_order !== undefined ? `秩序 ${met.metrics.sect_order}% · 灵压稳定` : '平稳运转 · 灵压稳定');
        UI.guardArray.innerText = arrayStatus;
        UI.guardDetail.innerText = met.memory?.watchdog_snapshot?.last_check_time
            ? `巡检：${met.memory.watchdog_snapshot.last_check_time}`
            : '巡检时间未载入';
        const progressText = met.system.progress_hint !== undefined ? ` · 进度 ${met.system.progress_hint}%` : '';
        UI.currentPath.innerText = `${met.system.current_path || met.system.state || '静修'}${progressText}`;
        UI.cadence.innerText = met.cron
            ? `${met.cron.cadence} · 巡天令 ${met.cron.job_count || 0} 道`
            : '巡天未启';

        if(met.memory) {
            UI.memoryDepth.innerText = met.memory.memory_depth || '未测';
            UI.memoryScale.innerText = `${met.memory.memory_chars || 0} 字 / ${met.memory.memory_lines || 0} 行`;
            UI.memoryHighlights.innerText = (met.memory.memory_highlights || []).slice(0, 4).join('\n') || '尚未探入识海深处。';
        }
        if(met.cron) {
            UI.heartbeatState.innerText = met.cron.heartbeat_enabled ? '心跳常明' : '心跳未启';
            UI.heartbeatReport.innerText = met.cron.heartbeat_last_report || met.cron.heartbeat_last_summary || '暂无巡天落印';
        }
        if(met.offline) {
            showOfflineSettlementCard(met.offline);
        }
        
        
        let sectCard = document.getElementById('pSectName');
        if(sectCard) {
            sectCard.innerText = met.sect.name || "OpenClaw 本源门";
            const subagentCountEl = document.getElementById('pSectSubagentCount');
            const subagentPressureEl = document.getElementById('pSectSubagentPressure');
            if(subagentCountEl) subagentCountEl.innerText = met.subagents?.count ?? 0;
            if(subagentPressureEl) subagentPressureEl.innerText = `${met.subagents?.pressure ?? 0}%`;
            let ul = document.getElementById('pSectSkills');
            ul.innerHTML = "";
            (met.sect.skills || []).forEach(skill => {
                let li = document.createElement('li');
                li.style.cssText = "background:rgba(0,120,255,0.2); border:1px solid #0ff; padding:2px 6px; border-radius:4px; font-size:11px; color:#fff;";
                li.innerText = "◈ " + skill;
                ul.appendChild(li);
            });
            
            const procContainer = document.getElementById('pSectProcesses');
            if (procContainer) {
                procContainer.innerHTML = '';
                (met.subagents?.processes || []).slice(0, 6).forEach(proc => {
                    const row = document.createElement('div');
                    row.title = `PID ${proc.pid} · CPU ${proc.cpu}% · MEM ${proc.mem}%`;
                    row.style.cssText = 'padding:8px 10px; border-radius:12px; border:1px solid rgba(255,255,255,0.08); background:rgba(255,255,255,0.04); font-size:12px; color:#dffbff;';
                    row.innerText = `${proc.comm} · PID ${proc.pid} · CPU ${proc.cpu}% · MEM ${proc.mem}%`;
                    procContainer.appendChild(row);
                });
            }

            let d_container = document.getElementById('pSectDivisions');
            d_container.innerHTML = "";
            let divs = met.sect.divisions || {};
            for(let hall in divs) {
                let dinfo = divs[hall];
                let col = document.createElement('div');
                col.style.cssText = "background:rgba(0,0,0,0.4); padding:8px; border-left:2px solid #0ff;";
                
                let title = document.createElement('div');
                title.style.cssText = "font-weight:bold; font-size:13px; color:#0ff;";
                title.innerText = hall + " [" + dinfo.assigned.length + "人]";
                
                let desc = document.createElement('div');
                desc.style.cssText = "font-size:10px; color:#aaa; margin-bottom:5px;";
                desc.innerText = dinfo.desc;
                
                let btn = document.createElement('button');
                btn.innerText = "+ 祭分神";
                btn.style.cssText = "background:none; border:1px solid #f1c40f; color:#f1c40f; font-size:10px; padding:2px 6px; cursor:pointer;";
                btn.onclick = () => { dispatchAvatar(hall) };
                
                col.appendChild(title);
                col.appendChild(desc);
                const realSubagents = (met.subagents?.subagents || []).filter(item => item.hall === hall);
                let status = document.createElement('div');
                status.style.cssText = "font-size:10px; color:#8ad7ff; margin-bottom:6px;";
                status.innerText = dinfo.assigned.length > 0
                    ? `堂口活跃 · 已开 ${dinfo.assigned.length} 化身 / 真并行 ${realSubagents.length}`
                    : (realSubagents.length > 0 ? `堂口受命 · 真并行 ${realSubagents.length}` : "堂口未启 · 可祭分神");
                col.appendChild(status);
                if(dinfo.assigned.length > 0) {
                   let alist = document.createElement('div');
                   alist.style.cssText = "font-size:11px; color:#fff; margin-bottom:6px; line-height:1.5;";
                   alist.innerText = dinfo.assigned.join(", ");
                   col.appendChild(alist);
                }

                if(realSubagents.length > 0) {
                   let realList = document.createElement('div');
                   realList.style.cssText = "font-size:10px; color:#cdefff; margin-bottom:6px; line-height:1.6; opacity:0.86;";
                   realList.innerText = realSubagents.map(item => `${item.name}（${item.status}）`).join("\n");
                   col.appendChild(realList);
                }
                col.appendChild(btn);
                
                d_container.appendChild(col);
            }
        }
        
        if(!AppState.isProcessing) {
            AppState.demon = met.metrics.inner_demon;
            UI.demon.innerText = AppState.demon + "%";
            UI.luck.innerText = met.metrics.fortune_chance > 50 ? "天命" : "凶煞";
            setRealmDamageState(met.rebirth_watchdog?.triggered && met.rebirth_watchdog?.trigger_reason === 'context_overflow' ? true : UI.stage?.classList.contains('realm-damaged'));
            
            if(AppState.demon > 60) {
                UI.bg.style.backgroundImage = `url(${Assets.bgDemon})`;
                UI.bg.style.filter = "hue-rotate(270deg) contrast(1.2)";
                UI.btnSuppress.style.display = 'block';
                const railBtn = document.getElementById('btnSuppressRail');
                if (railBtn) railBtn.style.display = 'block';
            } else {
                UI.bg.style.backgroundImage = `url(${Assets.bg})`;
                UI.bg.style.filter = "brightness(1)";
                UI.btnSuppress.style.display = 'none';
                const railBtn = document.getElementById('btnSuppressRail');
                if (railBtn) railBtn.style.display = 'none';
            }
            
            if(met.realm.cultivation_points >= met.realm.breakthrough_threshold) {
                document.getElementById('btnBreak').style.animation = "float 1s infinite alternate";
                document.getElementById('btnBreak').style.background = "rgba(241, 196, 15, 0.4)";
                UI.cultPoints.style.color = "#f1c40f";
            } else {
                document.getElementById('btnBreak').style.animation = "none";
                document.getElementById('btnBreak').style.background = "rgba(10, 20, 35, 0.8)";
                UI.cultPoints.style.color = "#0ff";
            }
        }
    } catch(e) {}
}

function closeAllOverlays() {
    document.getElementById('sectCard')?.classList.add('hidden');
    document.body.classList.remove('sect-mode');
    UI.memoryDrawer?.classList.remove('open');
}

window.switchPage = function(page) {
    if(page === 'sect') {
        closeAllOverlays();
        document.body.classList.add('sect-mode');
        document.getElementById('sectCard').classList.remove('hidden');
        return;
    }
    if(page === 'memory') {
        closeAllOverlays();
        UI.memoryDrawer.classList.add('open');
        if(!AppState.memoryLoaded) loadInsightLog();
        return;
    }
    if(page === 'close-memory') {
        UI.memoryDrawer.classList.remove('open');
    }
}


function renderActiveEvent(ev) {
    if(ev) {
        UI.activeEventText.innerText = `${ev.type || '外缘'} · ${ev.title || '未名波动'}`;
        UI.activeEventCard.classList.remove('hidden');
    } else {
        UI.activeEventText.innerText = '暂无未决机缘';
        UI.activeEventCard.classList.add('hidden');
    }
}

function hydrateEventCard(ev) {
    
    document.getElementById('ecmType').innerText = ev.type || '系统急令';
    document.getElementById('ecmTitle').innerText = ev.title || '识海异动';
    document.getElementById('ecmDesc').innerText = ev.desc || ev.content || '前尘卷宗，是否前往一探？';
    UI.eventWeight.innerText = ev.weight !== undefined ? `${ev.weight} 重` : '未测';
    UI.eventTime.innerText = ev.ts ? formatTs(ev.ts) : '刚刚';
    const confirmBtn = document.getElementById('eventConfirmBtn');
    const rejectBtn = document.getElementById('eventRejectBtn');
    if (confirmBtn && ev.choice_a && ADVENTURE_CHOICES[ev.choice_a]) confirmBtn.innerText = ADVENTURE_CHOICES[ev.choice_a].label;
    if (rejectBtn && ev.choice_b && ADVENTURE_CHOICES[ev.choice_b]) rejectBtn.innerText = ADVENTURE_CHOICES[ev.choice_b].label;
    renderActiveEvent(ev);
    UI.eventCard.classList.remove('hidden');
    AppState.isProcessing = true;
}

async function checkEvent() {
    if(AppState.isProcessing) return;
    try {
        const [ev, met] = await Promise.all([
            safeJsonFetch(`/data/current_event.json?v=${Date.now()}`, null),
            safeJsonFetch(`/api/state?v=${Date.now()}`, null)
        ]);
        if(!met) return;
        const demon = met?.metrics?.inner_demon || 0;
        const purity = met?.metrics?.path_purity || 0;
        if((demon >= 68 || purity >= 78) && ev) {
            currentEvent = ev;
            hydrateEventCard(ev);
            return;
        }
        if(!ev && Math.random() < 0.35) {
            currentEvent = buildAdventureEvent(met);
            hydrateEventCard(currentEvent);
            return;
        }
        if(ev && Math.random() < 0.6) {
            currentEvent = ev;
            hydrateEventCard(ev);
        }
    } catch(e) {}
}

window.resolveAdventure = function(acceptPrimary) {
    UI.eventCard.classList.add('hidden');
    UI.eventCard.style.display = 'none';
    requestAnimationFrame(() => { UI.eventCard.style.display = ''; });
    const key = acceptPrimary ? currentEvent?.choice_a : currentEvent?.choice_b;
    const choice = ADVENTURE_CHOICES[key] || null;
    if(choice) {
        log(choice.accept_msg, acceptPrimary ? '#1dd1a1' : '#ffcc00');
        showToast(`${choice.label}：${choice.desc}`, acceptPrimary ? '#7ef9ff' : '#ffd36b');
    } else if(acceptPrimary) {
        log(currentEvent?.accept_msg || `已承接【${currentEvent?.title || '无名机缘'}】。`, "#1dd1a1");
    } else {
        log(currentEvent?.reject_msg || `暂避【${currentEvent?.title || '无名机缘'}】，不染尘劫。`, "#ffcc00");
    }
    renderActiveEvent(null);
    currentEvent = null;
    AppState.modalLocked = false;
    resetState("事件结束。");
}

window.closeFateCard = function() {
    UI.fateCard.classList.add('hidden');
    UI.fateCard.style.display = 'none';
    requestAnimationFrame(() => { UI.fateCard.style.display = ''; });
    AppState.modalLocked = false;
}

window.closeSectFateCard = function() {
    UI.sectFateCard.classList.add('hidden');
    UI.sectFateCard.style.display = 'none';
    requestAnimationFrame(() => { UI.sectFateCard.style.display = ''; });
    AppState.modalLocked = false;
}

window.claimOfflineSettlement = async function() {
    try {
        const currentStamp = UI.offlineCalculatedAt?.innerText || null;
        const res = await fetch('/api/action/claim_offline', { method: 'POST' });
        const data = await res.json();
        UI.offlineSettlementCard.classList.add('hidden');
        AppState.offlineClaimedAt = currentStamp;
        AppState.modalLocked = false;
        appendSystemMessage(data.narrative || '离线闭关结算完成。', '#ffd36b');
        fetchData();
    } catch(e) {
        appendSystemMessage('离线结算通路受阻，暂未能收束闭关所得。', '#ff8a8a');
    }
}

window.dismissOfflineSettlement = function() {
    AppState.offlineDismissedAt = UI.offlineCalculatedAt?.innerText || null;
    UI.offlineSettlementCard.classList.add('hidden');
    AppState.modalLocked = false;
}

window.toggleChatDock = function() {
    const dock = document.getElementById('chatDock');
    const btn = document.querySelector('.chat-collapse-btn');
    if(!dock) return;
    dock.classList.toggle('collapsed');
    if(btn) btn.innerText = dock.classList.contains('collapsed') ? '⌃' : '⌄';
}

window.toggleChatTools = function() {
    const menu = document.getElementById('chatToolMenu');
    if(menu) menu.classList.toggle('hidden');
}

window.triggerImageUpload = function() {
    const input = document.getElementById('imageUploadInput');
    if(input) input.click();
}

window.handleImageUpload = function(event) {
    const file = event?.target?.files?.[0];
    if(!file) return;
    appendSystemMessage(`已感应灵图《${file.name}》 (${Math.max(1, Math.round(file.size / 1024))} KB)，后续可接入图像法器解析。`, '#ffd36b');
    event.target.value = '';
}

window.ackOnboarding = async function() {
    if (AppState.onboardingSteps?.length && AppState.onboardingIndex < AppState.onboardingSteps.length - 1) {
        advanceOnboardingStep();
        return;
    }
    const overlay = document.getElementById('introOverlay');
    try {
        await fetch('/api/onboarding/ack', { method: 'POST' });
    } catch (e) {
        console.warn('[dragon-lobster] onboarding ack failed', e);
    }
    document.getElementById('introSpotlight')?.classList.add('hidden');
    if(overlay) {
        overlay.classList.add('hidden');
        setTimeout(() => overlay.classList.add('finished'), 800);
    }
}

window.rebirthNow = async function() {
    try {
        const res = await fetch('/api/action/rebirth', { method: 'POST' });
        const data = await res.json();
        appendSystemMessage(data.narrative || '兵解完成。', '#ffd36b');
        fetchData();
    } catch (e) {
        appendSystemMessage('兵解法门暂时失灵。', '#ff8a8a');
    }
}

window.handleChatInputKey = function(event) {
    if(event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

window.sendChatMessage = async function() {
    const input = getChatInput();
    const text = input?.value?.trim();
    if(!text) return;

    appendSystemMessage(`你：${text}`, '#9ce9ff');
    if(input) input.value = '';

    try {
        const res = await fetch('/api/chat/parse', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text})
        });
        const data = await res.json();
        appendSystemMessage(data.reply || '器灵暂无回应。', data.color || '#d0f0ff');
        if(data.command) {
            appendSystemMessage(`器灵解意：${data.command}`, '#ffd36b');
        }
    } catch(e) {
        appendSystemMessage('飞符通道尚未稳定，器灵暂时失联。', '#ff8a8a');
    }
}

window.init = init;
document.addEventListener("DOMContentLoaded", init);


async function pollChatEchoes() {
    try {
        const text = await fetch(`/data/chat_echoes.jsonl?v=${Date.now()}`).then(r => r.text()).catch(() => '');
        const items = text.split('\n').map(line => line.trim()).filter(Boolean).map(line => {
            try { return JSON.parse(line); } catch { return null; }
        }).filter(Boolean);
        if(!items.length) return;
        const fresh = items.filter(item => !AppState.seenChatEchoTs || item.ts > AppState.seenChatEchoTs);
        if(!fresh.length) return;
        fresh.forEach(item => {
            const prefix = item.role === 'user' ? '传念回响' : '天降卷宗';
            appendSystemMessage(`【${prefix}】${item.content}`, item.role === 'user' ? '#8ad7ff' : '#ffd36b');
        });
        AppState.seenChatEchoTs = fresh[fresh.length - 1].ts;
    } catch (e) {
        console.warn('[dragon-lobster] poll chat echoes failed', e);
    }
}

async function loadInsightLog() {
    try {
        const [insightRes, state] = await Promise.all([
            fetch(`/data/insight_log.jsonl?v=${Date.now()}`).then(r => r.text()).catch(() => ''),
            safeJsonFetch(`/api/state?v=${Date.now()}`, { memory: { recent_items: [] } })
        ]);
        const text = insightRes;
        const items = text.split('\n').map(line => line.trim()).filter(Boolean).map(line => {
            try { return JSON.parse(line); } catch { return null; }
        }).filter(Boolean).slice(-8).reverse();

        const learningItems = (state.memory?.recent_items || []).map(item => ({
            type: item.type || '悟道',
            title: item.title || item.type || '识海条目',
            content: item.content || '',
            ts: null
        }));

        const mergedItems = [...learningItems, ...items].slice(0, 10);

        UI.memoryList.innerHTML = '';
        mergedItems.forEach(item => {
            const row = document.createElement('div');
            row.className = `memory-item type-${item.type || 'default'}`;
            row.innerHTML = `
              <div class="memory-topline">
                <span class="memory-type">${item.type || '记录'}</span>
                <span class="memory-time">${item.ts ? formatTs(item.ts) : '识海常驻'}</span>
              </div>
              <div class="memory-title">${item.title || '无题道痕'}</div>
              <div class="memory-content">${item.content || ''}</div>
            `;
            UI.memoryList.appendChild(row);
        });
        AppState.memoryLoaded = true;
    } catch(e) {
        if(!AppState.memoryLoaded) {
            UI.memoryList.innerHTML = '<div class="memory-empty">识海尚未显形，暂时无可回溯道痕。</div>';
        }
    }
}

function formatTs(ts) {
    if(!ts) return '未记时';
    const d = new Date(ts);
    if(Number.isNaN(d.getTime())) return ts;
    return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

window.dispatchAvatar = async function(hallName) {
    if(AppState.isProcessing) {
        log("神识被占，无法开辟分神化身！", "#ff4d4d");
        return;
    }
    const task = window.prompt(`为【${hallName}】下达真实任务：`, `前往${hallName}执行搜索任务`);
    if(task === null) return;
    log(`正在本源分裂，指派化身前往【${hallName}】...`, "#0ff");
    AppState.isProcessing = true;
    try {
        const res = await fetch("/api/action/sect_dispatch", { 
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({hall: hallName, task})
        });
        const data = await res.json();
        resetState(data.narrative);
        if(data.sect_fate) {
            showSectFateCard(data.sect_fate, data.narrative);
        }
        fetchData(); // 马上刷新UI
    } catch(e) {
        resetState("化身剥离失败：天机错乱。");
    }
}
