/**
 * bugManagement.js
 * Used by BOTH Manager (bugManagement.html) and Engineer (engineerBugManagement.html).
 *
 * Table columns: PRIORITY | BUG ID | ENGINEER | TESTS | ACTION
 * (Summary, Stations, Station Config, Resource Group removed)
 *
 * Each bug row expands to show:
 *   - Test sub-table (test name, station, nodes, ring, build)
 *   - ML Analysis panel (repro actions, config changes, repro readiness, summary)
 */

const API_BASE = '';

let currentUser        = null;
let workgroups         = [];
let engineers          = [];
let currentFilter      = 'all';
let bugOwnershipFilter = 'workgroup';
let activeWorkgroupId  = null;
let allReproBugs       = [];
let allTestBugs        = [];

function getAuthHeaders(headers = {}) {
    return window.RROAuth ? window.RROAuth.getAuthHeaders(headers) : headers;
}

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
    userName:               $('#userName'),
    userAvatar:             $('#userAvatar'),
    userRoleBadge:          $('#userRoleBadge'),
    profileDropdownTrigger: $('#profileDropdownTrigger'),
    profileDropdown:        $('#profileDropdown'),
    profileEmail:           $('#profileEmail'),
    btnLogout:              $('#btnLogout'),
    statTotalBugs:          $('#statTotalBugs'),
    statReproBugs:          $('#statReproBugs'),
    statTestBugs:           $('#statTestBugs'),
    statPendingActions:     $('#statPendingActions'),
    reproBugsCount:         $('#reproBugsCount'),
    testBugsCount:          $('#testBugsCount'),
    reproBugsBody:          $('#reproBugsBody'),
    testBugsBody:           $('#testBugsBody'),
    searchInput:            $('#searchInput'),
    searchDropdown:         $('#searchDropdown'),
    ownershipFilter:        $('#ownershipFilter'),
    filterWorkgroupBugs:    $('#filterWorkgroupBugs'),
    filterMyBugs:           $('#filterMyBugs'),
};

/* ── API Helper ── */
async function apiFetch(path, options = {}) {
    try {
        const res = await fetch(`${API_BASE}${path}`, {
            headers: getAuthHeaders({ 'Content-Type': 'application/json', ...options.headers }),
            credentials: 'include',
            ...options,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
        return await res.json();
    } catch (err) {
        console.warn(`[API] ${options.method || 'GET'} ${path} → ${err.message}`);
        return null;
    }
}

/* ── Utilities ── */
function escapeHtml(str) {
    if (str == null) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function animateNumber(el, target) {
    if (!el) return;
    const duration = 500;
    const start    = (el.textContent === '—' || el.textContent === '')
        ? 0 : parseInt(el.textContent) || 0;
    if (start === target) { el.textContent = target; return; }
    const t0 = performance.now();
    function tick(now) {
        const p    = Math.min((now - t0) / duration, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(start + (target - start) * ease);
        if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

function nodeLabel(n) {
    if (!n) return '—';
    return Array.from({ length: n }, (_, i) => `N${i + 1}`).join('/');
}

/* ── Workgroup / filter helpers ── */
function getCurrentWorkgroupId() {
    return new URLSearchParams(window.location.search).get('workgroup_id');
}

function shouldShowEngineerOwnershipFilter() {
    return currentUser?.role === 'Engineer' && !activeWorkgroupId;
}

function buildBugQueryParams(extraParams = {}) {
    const params = new URLSearchParams();
    if (activeWorkgroupId) params.set('workgroup_id', activeWorkgroupId);
    if (shouldShowEngineerOwnershipFilter() && bugOwnershipFilter === 'mine') {
        params.set('my_only', 'true');
    }
    Object.entries(extraParams).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
            params.set(key, String(value));
        }
    });
    return params;
}

function updateOwnershipFilterUi() {
    if (!dom.ownershipFilter || !dom.filterWorkgroupBugs || !dom.filterMyBugs) return;
    const show = shouldShowEngineerOwnershipFilter();
    dom.ownershipFilter.classList.toggle('hidden', !show);
    dom.filterWorkgroupBugs.classList.toggle('active', bugOwnershipFilter === 'workgroup');
    dom.filterMyBugs.classList.toggle('active', bugOwnershipFilter === 'mine');
}

/* ── Data Loaders ── */
async function loadCurrentUser() {
    const data  = await apiFetch('/api/auth/me');
    currentUser = data || { id: 1, name: 'User', fullName: 'User', email: '', role: 'Manager' };
    renderUserInfo();
}

async function loadBugsData() {
    const params    = buildBugQueryParams();
    const qs        = params.toString();
    const apiPath   = qs ? `/api/bugs?${qs}` : '/api/bugs';
    const statsPath = qs ? `/api/bugs/stats?${qs}` : '/api/bugs/stats';

    console.log('Loading bugs from:', apiPath);
    const data  = await apiFetch(apiPath);
    console.log('Bugs data received:', data);
    const stats = await apiFetch(statsPath);
    console.log('Stats data received:', stats);

    if (stats) renderStats(stats);
    if (data) {
        allReproBugs = data.repro || [];
        allTestBugs  = data.test  || [];
        renderBugs(allReproBugs, allTestBugs);
    }
}

async function refreshAll() {
    await Promise.all([loadBugsData()]);
}

async function setBugOwnershipFilter(nextFilter) {
    if (bugOwnershipFilter === nextFilter) return;
    bugOwnershipFilter = nextFilter;
    updateOwnershipFilterUi();
    if (dom.searchInput)    dom.searchInput.value = '';
    if (dom.searchDropdown) dom.searchDropdown.classList.add('hidden');
    await loadBugsData();
}

/* ── Renderers: User & Stats ── */
function renderUserInfo() {
    if (!currentUser) return;
    if (dom.userAvatar) dom.userAvatar.classList.remove('loading-pulse');
    if (dom.userName)   dom.userName.classList.remove('loading-text');

    const initials = currentUser.fullName
        ? currentUser.fullName.split(' ').map(n => n[0]).join('').toUpperCase()
        : currentUser.name[0].toUpperCase();

    if (dom.userAvatar)    dom.userAvatar.textContent    = initials;
    if (dom.userName)      dom.userName.textContent      = currentUser.fullName || currentUser.name;
    if (dom.userRoleBadge) dom.userRoleBadge.textContent = currentUser.role || 'Manager';
    if (dom.profileEmail)  dom.profileEmail.textContent  = currentUser.email || 'manager@rro.com';

    updateOwnershipFilterUi();
}

function renderStats(stats) {
    animateNumber(dom.statTotalBugs,      stats.totalBugs);
    animateNumber(dom.statReproBugs,      stats.reproBugs);
    animateNumber(dom.statTestBugs,       stats.testBugs);
    animateNumber(dom.statPendingActions, stats.pendingActions);
}

/* ── Renderers: Bug Tables ── */

/**
 * Builds TWO <tr> elements per bug:
 *   1. Collapsed row: PRIORITY | BUG ID | ENGINEER | TESTS badge | ACTION
 *   2. Hidden expansion row: test sub-table + ML Analysis panel
 */
function generateBugRowHtml(bug) {
    const bugId     = escapeHtml(bug.id);
    const testCount = bug.test_count ?? (bug.tests ? bug.tests.length : 0);
    const pClass    = {
        P0: 'priority-p0', P1: 'priority-p1', P2: 'priority-p2',
        P3: 'priority-p3', P4: 'priority-p4',
    }[bug.priority] || 'priority-p2';

    const mainRow = `
    <tr class="bug-row" data-bug-id="${bugId}"
        onmouseenter="this.style.backgroundColor='#f1f5f9'"
        onmouseleave="this.style.backgroundColor=''">
        <td>
            <span class="priority-badge ${pClass}">${escapeHtml(bug.priority || 'P2')}</span>
        </td>
        <td class="bug-id-cell">${bugId}</td>
        <td>
            <div class="engineer-cell">
                <div class="engineer-avatar" style="background:${escapeHtml(bug.engineer.color)}">
                    ${escapeHtml(bug.engineer.initials)}
                </div>
                <span class="engineer-name">${escapeHtml(bug.engineer.name)}</span>
            </div>
        </td>
        <td>
            <span style="background:#eff6ff;color:#2563eb;padding:4px 10px;border-radius:6px;
                         font-size:11.5px;font-weight:600;cursor:pointer;
                         display:inline-flex;align-items:center;gap:6px;user-select:none;"
                  onclick="toggleBugExpand('${bugId}', this)">
                ${testCount} Tests
                <svg class="expand-arrow" width="12" height="12" viewBox="0 0 12 12"
                     fill="none" style="transition:transform 0.25s;flex-shrink:0;">
                    <polygon points="2,4 10,4 6,9" fill="#2563eb"/>
                </svg>
            </span>
        </td>
        <td>
            <div class="action-cell">
                <button class="btn-action btn-run" onclick="runBugNow('${bugId}')">
                    <svg width="12" height="12" viewBox="0 0 16 16" fill="none"
                         stroke="currentColor" stroke-width="2"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 3L12 8L4 13V3Z" fill="currentColor" stroke="none"/>
                    </svg>
                    Run Now
                </button>
                <button class="btn-action btn-later" onclick="scheduleBug('${bugId}')">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none"
                         stroke="currentColor" stroke-width="1.5"
                         stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="8" cy="8" r="7"/>
                        <path d="M8 4V8L11 10"/>
                    </svg>
                    Run Later
                </button>
            </div>
        </td>
    </tr>`;

    const expandRow = `
    <tr id="expand-${bugId}" style="display:none;">
        <td colspan="5" style="padding:0;background:#f8fafc;border-bottom:2px solid #e2e8f0;">
            <div style="padding:16px 24px;">
                <div id="tests-content-${bugId}">
                    <span style="color:#94a3b8;font-size:13px;">Loading tests…</span>
                </div>
                <div id="analysis-content-${bugId}" style="margin-top:14px;display:none;">
                    <span style="color:#94a3b8;font-size:13px;">Loading ML Analysis…</span>
                </div>
            </div>
        </td>
    </tr>`;

    return mainRow + expandRow;
}

function generateBugsTableRows(bugs) {
    if (!bugs || bugs.length === 0) return '';
    return bugs.map(generateBugRowHtml).join('');
}

function renderBugs(reproBugs, testBugs) {
    console.log('Rendering repro bugs:', reproBugs);
    console.log('Rendering test bugs:', testBugs);

    if (dom.reproBugsCount) dom.reproBugsCount.textContent = `${reproBugs.length} bugs`;
    if (dom.testBugsCount)  dom.testBugsCount.textContent  = `${testBugs.length} bugs`;
    if (dom.reproBugsBody)  dom.reproBugsBody.innerHTML     = generateBugsTableRows(reproBugs);
    if (dom.testBugsBody)   dom.testBugsBody.innerHTML      = generateBugsTableRows(testBugs);
}

/* ── Expandable Row Logic ── */

async function toggleBugExpand(bugId, badgeEl) {
    const expandRow = document.getElementById(`expand-${bugId}`);
    if (!expandRow) return;

    const arrow  = badgeEl.querySelector('.expand-arrow');
    const isOpen = expandRow.style.display !== 'none';

    if (isOpen) {
        expandRow.style.display = 'none';
        if (arrow) arrow.style.transform = 'rotate(0deg)';
        return;
    }

    expandRow.style.display = 'table-row';
    if (arrow) arrow.style.transform = 'rotate(180deg)';

    const testsDiv    = document.getElementById(`tests-content-${bugId}`);
    const analysisDiv = document.getElementById(`analysis-content-${bugId}`);

    if (testsDiv && testsDiv.dataset.loaded !== 'true') {
        testsDiv.dataset.loaded = 'true';
        await fetchAndRenderTests(bugId, testsDiv);
    }
    if (analysisDiv && analysisDiv.dataset.loaded !== 'true') {
        analysisDiv.dataset.loaded = 'true';
        await loadMLAnalysis(bugId, analysisDiv);
    }
}

async function fetchAndRenderTests(bugId, testsDiv) {
    try {
        const res = await apiFetch(`/api/bugs/${bugId}/tests`);

        if (!res || !res.tests || res.tests.length === 0) {
            testsDiv.innerHTML =
                `<span style="color:#94a3b8;font-size:13px;">No test data available.</span>`;
            return;
        }

        let html = `
            <div style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;
                        letter-spacing:0.5px;margin-bottom:8px;">Test Details</div>
            <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:12.5px;background:#fff;
                          border-radius:6px;border:1px solid #e2e8f0;">
                <thead>
                    <tr style="background:#e2e8f0;">
                        <th style="padding:8px 12px;text-align:left;color:#475569;font-size:11px;font-weight:600;text-transform:uppercase;">Test Name</th>
                        <th style="padding:8px 12px;text-align:left;color:#475569;font-size:11px;font-weight:600;text-transform:uppercase;">Station</th>
                        <th style="padding:8px 12px;text-align:left;color:#475569;font-size:11px;font-weight:600;text-transform:uppercase;">Nodes</th>
                        <th style="padding:8px 12px;text-align:left;color:#475569;font-size:11px;font-weight:600;text-transform:uppercase;">Ring</th>
                        <th style="padding:8px 12px;text-align:left;color:#475569;font-size:11px;font-weight:600;text-transform:uppercase;">Build</th>
                    </tr>
                </thead>
                <tbody>`;

        res.tests.forEach(t => {
            html += `
                <tr style="border-bottom:1px solid #e2e8f0;">
                    <td style="padding:8px 12px;">${escapeHtml(t.test_name || '—')}</td>
                    <td style="padding:8px 12px;">${escapeHtml(t.station_name || t.test_ring_name || '—')}</td>
                    <td style="padding:8px 12px;">${escapeHtml(nodeLabel(t.number_of_nodes))}</td>
                    <td style="padding:8px 12px;">${escapeHtml(t.test_ring_name || '—')}</td>
                    <td style="padding:8px 12px;">${escapeHtml(t.build_version || '—')}</td>
                </tr>`;
        });

        html += `</tbody></table></div>
            <button onclick="toggleMLAnalysis('${escapeHtml(bugId)}')"
                    style="margin-top:12px;background:#7c3aed;color:white;border:none;
                           padding:7px 16px;border-radius:6px;font-size:12px;cursor:pointer;
                           display:inline-flex;align-items:center;gap:6px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>
                </svg>
                Show ML Analysis
            </button>`;

        testsDiv.innerHTML = html;
    } catch (e) {
        testsDiv.innerHTML =
            `<span style="color:#ef4444;font-size:13px;">Failed to load tests.</span>`;
    }
}

function toggleMLAnalysis(bugId) {
    const div = document.getElementById(`analysis-content-${bugId}`);
    if (!div) return;
    div.style.display = div.style.display === 'none' ? 'block' : 'none';
}

async function loadMLAnalysis(bugId, div) {
    try {
        const res = await apiFetch(`/api/bugs/${bugId}/analysis`);

        if (!res || !res.analysis) {
            div.innerHTML =
                `<p style="color:#94a3b8;font-size:13px;">No ML analysis available yet.</p>`;
            return;
        }

        const a = res.analysis;
        div.innerHTML = `
            <div style="background:#f5f3ff;border-radius:8px;padding:16px;border-left:3px solid #7c3aed;">
                <h4 style="margin:0 0 14px;font-size:13px;color:#7c3aed;font-weight:700;">
                    🤖 ML Analysis (ChatHPE)
                </h4>
                <div style="margin-bottom:12px;">
                    <span style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.4px;">Repro Actions</span>
                    <p style="margin:4px 0 0;font-size:12.5px;color:#334155;line-height:1.5;">${escapeHtml(a.repro_actions || '—')}</p>
                </div>
                <div style="margin-bottom:12px;">
                    <span style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.4px;">Config Changes</span>
                    <p style="margin:4px 0 0;font-size:12.5px;color:#334155;line-height:1.5;">${escapeHtml(a.config_changes || '—')}</p>
                </div>
                <div style="margin-bottom:12px;">
                    <span style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.4px;">Repro Readiness</span>
                    <p style="margin:4px 0 0;font-size:12.5px;color:#334155;line-height:1.5;">${escapeHtml(a.repro_readiness || '—')}</p>
                </div>
                <div>
                    <span style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.4px;">Summary</span>
                    <p style="margin:4px 0 0;font-size:12.5px;color:#334155;line-height:1.5;">${escapeHtml(a.summary || '—')}</p>
                </div>
            </div>`;
    } catch (e) {
        div.innerHTML =
            `<p style="color:#ef4444;font-size:13px;">Failed to load ML analysis.</p>`;
    }
}

/* ── Bug Actions ── */
async function runBugNow(bugId) {
    await apiFetch(`/api/bugs/${bugId}/run`, { method: 'POST' });
    await loadBugsData();
}

async function scheduleBug(bugId) {
    await apiFetch(`/api/bugs/${bugId}/schedule`, { method: 'POST' });
    await loadBugsData();
}

/* ── Dynamic Search ── */
let searchDebounceTimer = null;

function highlightMatch(text, query) {
    if (!query) return escapeHtml(text);
    const escaped = escapeHtml(text);
    const regex   = new RegExp(
        `(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'
    );
    return escaped.replace(regex, '<mark>$1</mark>');
}

function getTagClass(type) {
    switch (type) {
        case 'Bug ID':   return 'search-dropdown-tag--bugid';
        case 'Engineer': return 'search-dropdown-tag--engineer';
        case 'Test':     return 'search-dropdown-tag--test';
        case 'Station':  return 'search-dropdown-tag--station';
        default:         return '';
    }
}

function renderSearchDropdown(suggestions, query) {
    if (!suggestions || suggestions.length === 0) {
        dom.searchDropdown.innerHTML = `
            <div class="search-dropdown-empty">
                <span>No results found for "<strong>${escapeHtml(query)}</strong>"</span>
            </div>`;
        dom.searchDropdown.classList.remove('hidden');
        return;
    }

    const html = suggestions.map(s => `
        <div class="search-dropdown-item"
             data-type="${escapeHtml(s.type)}"
             data-value="${escapeHtml(s.value)}"
             data-bugcode="${escapeHtml(s.bug_code)}">
            <span class="search-dropdown-tag ${getTagClass(s.type)}">${escapeHtml(s.type)}</span>
            <span class="search-dropdown-value">${highlightMatch(s.value, query)}</span>
        </div>
    `).join('');

    dom.searchDropdown.innerHTML = html;
    dom.searchDropdown.classList.remove('hidden');

    dom.searchDropdown.querySelectorAll('.search-dropdown-item').forEach(item => {
        item.addEventListener('click', () => {
            dom.searchInput.value = item.dataset.value;
            dom.searchDropdown.classList.add('hidden');
            filterBugsBySelection(item.dataset.type, item.dataset.value);
        });
    });
}

function filterBugsBySelection(type, value) {
    const valueLower = value.toLowerCase();
    function bugMatches(bug) {
        switch (type) {
            case 'Bug ID':   return bug.id.toLowerCase() === valueLower;
            case 'Engineer': return bug.engineer.name.toLowerCase() === valueLower;
            case 'Test':     return (bug.tests || []).some(t => t.toLowerCase() === valueLower);
            case 'Station':  return (bug.stations || []).some(s => s.toLowerCase() === valueLower);
            default:         return false;
        }
    }
    renderBugs(allReproBugs.filter(bugMatches), allTestBugs.filter(bugMatches));
}

function resetBugTables() {
    renderBugs(allReproBugs, allTestBugs);
}

function handleSearchInput() {
    clearTimeout(searchDebounceTimer);
    const query = dom.searchInput.value.trim();
    if (!query) {
        dom.searchDropdown.classList.add('hidden');
        resetBugTables();
        return;
    }
    searchDebounceTimer = setTimeout(async () => {
        const params      = buildBugQueryParams({ q: query });
        const apiPath     = `/api/bugs/search?${params.toString()}`;
        const suggestions = await apiFetch(apiPath);
        if (suggestions !== null) renderSearchDropdown(suggestions, query);
    }, 250);
}

/* ── Close-all helper ── */
function closeAllDropdowns() {
    if (dom.profileDropdown) dom.profileDropdown.classList.add('hidden');
    if (dom.searchDropdown)  dom.searchDropdown.classList.add('hidden');
}

document.addEventListener('click', (e) => {
    const searchContainer = document.querySelector('.search-container');
    if (searchContainer && searchContainer.contains(e.target)) {
        if (dom.profileDropdown) dom.profileDropdown.classList.add('hidden');
        return;
    }
    closeAllDropdowns();
});

/* ── Event Listeners ── */
function initEventListeners() {
    if (dom.profileDropdownTrigger) {
        dom.profileDropdownTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            closeAllDropdowns();
            dom.profileDropdown.classList.toggle('hidden');
        });
    }

    if (dom.btnLogout) {
        dom.btnLogout.addEventListener('click', async () => {
            await apiFetch('/api/auth/logout', { method: 'POST' });
            if (window.RROAuth) window.RROAuth.clearToken();
            currentUser = null;
            window.location.href = '/';
        });
    }

    document.querySelectorAll('.bugs-header').forEach(header => {
        header.addEventListener('click', () => {
            const section = header.closest('.bugs-section');
            if (section) section.classList.toggle('collapsed');
        });
    });

    if (dom.searchInput) {
        dom.searchInput.addEventListener('input', handleSearchInput);
        dom.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') dom.searchDropdown.classList.add('hidden');
        });
    }

    if (dom.filterWorkgroupBugs) {
        dom.filterWorkgroupBugs.addEventListener('click', () => setBugOwnershipFilter('workgroup'));
    }
    if (dom.filterMyBugs) {
        dom.filterMyBugs.addEventListener('click', () => setBugOwnershipFilter('mine'));
    }
}

/* ── Init ── */
async function init() {
    activeWorkgroupId = getCurrentWorkgroupId();
    initEventListeners();
    await loadCurrentUser();
    updateOwnershipFilterUi();
    await loadBugsData();
}

document.addEventListener('DOMContentLoaded', init);