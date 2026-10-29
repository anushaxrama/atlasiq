const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? '—').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const fmt = (value, digits = 0) => value == null ? '—' : value.toLocaleString('en-US', { maximumFractionDigits: digits });
const money = (value) => value == null ? '—' : value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
const dateLabel = (value) => new Date(value + 'T12:00:00Z').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
});
const pageInfo = {
    overview: [
        'MOBILITY INTELLIGENCE / OVERVIEW',
        'The city, in motion.',
        'Understand how New York moves. One observed trip at a time.',
        'Overview',
    ],
    demand: [
        '02 / FOLLOW THE PATTERN',
        'Find the rhythm.',
        'Explore observed demand across days, hours and pickup zones.',
        'Demand explorer',
    ],
    zones: [
        '03 / A SENSE OF PLACE',
        'Place makes a difference.',
        'Compare real TLC pickup zones, with the local context intact.',
        'Zone comparison',
    ],
    weather: [
        '04 / THE CONDITIONS AROUND US',
        'A change in conditions.',
        'Daily station weather alongside observed trips. Association, not causation.',
        'Weather & demand',
    ],
    quality: [
        '05 / TRUST THE FOUNDATION',
        'Confidence, by design.',
        'Inspect the gates, warnings and limits behind the modeled data.',
        'Data quality',
    ],
    runs: [
        '06 / BEHIND THE REFRESH',
        'Behind every refresh.',
        'Real extraction, validation and publication runs—with their outcomes.',
        'Pipeline runs',
    ],
    methodology: [
        '07 / DEFINITIONS & BOUNDARIES',
        'The context behind the counts.',
        'A useful analytical product makes its assumptions visible.',
        'Methodology',
    ],
};
let meta;
let version = 0;
let offset = 0;
let currentPage = 'overview';
let appliedFilters = null;
async function api(path, params) {
    const response = await fetch('/api/' + path + (params ? '?' + params : ''), {
        signal: AbortSignal.timeout(20000),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(typeof error.detail === 'string'
            ? error.detail
            : `Warehouse request failed (${response.status})`);
    }
    return response.json();
}
function params(zone = true) {
    const p = new URLSearchParams({
        start: $('start').value,
        end: $('end').value,
    });
    const value = $('zone').value;
    if (zone && value)
        p.set('zone', value);
    return p;
}
const empty = (message = 'No observed trips match this view. Try a different date range or pickup zone.') => `<div class="empty">${esc(message)}</div>`;
function panel(title, subtitle, content, tag = 'OBSERVED / SAMPLE') {
    return `<article class="panel"><div class="panel-head"><div><div class="eyebrow">ATLAS / ANALYTICS</div><h2>${esc(title)}</h2><p>${esc(subtitle)}</p></div><span class="tag">${esc(tag)}</span></div>${content}</article>`;
}
const iconPaths = {
    overview: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    demand: '<path d="M3 18V6m0 12h18M6 14l4-5 4 3 6-7"/>',
    zones: '<path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2Zm6-2v16m6-14v16"/>',
    weather: '<path d="M8 17h10a4 4 0 0 0 .5-8A6 6 0 0 0 7 8a4.5 4.5 0 0 0 1 9Zm1 3-1 2m6-2-1 2m6-2-1 2"/>',
    quality: '<path d="m12 3 8 3v6c0 4-4 7-8 9-4-2-8-5-8-9V6Zm-4 9 3 3 5-6"/>',
    runs: '<path d="M3 11a9 9 0 1 1 2.5 7M3 4v7h7m2-5v6l4 2"/>',
    methodology: '<path d="M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-2H4Zm16 0h-4a3 3 0 0 0-3 3v14a4 4 0 0 1 4-2h3Z"/>',
    code: '<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18"/>',
    download: '<path d="M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5"/>',
    filter: '<path d="M4 6h16M7 12h10m-7 6h4"/>',
    fare: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 10h18m-5 5h2"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    median: '<path d="M4 8h16M4 16h16m-7-11 3 3-3 3m-2 2-3 3 3 3"/>',
    insight: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"/>',
};
const icon = (name) => `<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">${iconPaths[name] ?? iconPaths.overview}</svg>`;
document.querySelectorAll('[data-icon]').forEach((el) => {
    el.innerHTML = icon(el.dataset.icon);
});
function kpis(s) {
    return `<div class="kpi-grid">${[
        ['Trips observed', fmt(s.observed_trips), 'Accepted trips · selected sample', 'demand'],
        ['Average fare', money(s.average_fare_usd), 'Base fare · USD, excluding tips', 'fare'],
        [
            'Trip duration',
            fmt(s.average_duration_minutes, 1) + ' <span class="unit">min</span>',
            'Mean pickup-to-dropoff time',
            'clock',
        ],
        ['Median fare', money(s.median_fare_usd), '90th percentile ' + money(s.p90_fare_usd), 'median'],
    ]
        .map(([label, value, note, symbol]) => `<article class="kpi"><div class="kpi-label">${label}<span>${icon(symbol)}</span></div><div class="kpi-value">${value}</div><div class="kpi-note">${note}</div></article>`)
        .join('')}</div>`;
}
function line(rows, cumulative = false) {
    if (!rows.length)
        return empty();
    let running = 0;
    const values = rows.map((r) => (cumulative ? (running += r.observed_trips) : r.observed_trips));
    const rawMax = Math.max(...values, 1);
    const step = Math.max(1, Math.ceil(rawMax / 4 / 100) * 100);
    const max = step * 4;
    const x = (i) => 47 + (i / Math.max(rows.length - 1, 1)) * 618;
    const y = (n) => 220 - (n / max) * 190;
    const path = values.map((v, i) => `${i ? 'L' : 'M'}${x(i)},${y(v)}`).join(' ');
    let grid = '';
    for (let i = 0; i <= 4; i++) {
        const n = (max * i) / 4;
        grid += `<line class="grid" x1="47" x2="665" y1="${y(n)}" y2="${y(n)}"/><text x="35" y="${y(n) + 4}" text-anchor="end">${n >= 1000 ? fmt(n / 1000, 1) + 'k' : fmt(n)}</text>`;
    }
    const total = rows.reduce((sum, r) => sum + r.observed_trips, 0);
    const label = cumulative ? 'Cumulative trips' : 'Daily observed trip demand';
    return `<div class="trend-visual"><div class="chart-tools"><div class="chart-readout"><strong>${fmt(cumulative ? total : total / rows.length)} trips</strong> / ${cumulative ? 'selected window' : 'daily average'}</div><div class="chart-mode" aria-label="Chart aggregation"><button type="button" data-chart-mode="daily" aria-pressed="${!cumulative}">Daily</button><button type="button" data-chart-mode="cumulative" aria-pressed="${cumulative}">Cumulative</button></div></div><svg class="chart" viewBox="0 0 700 260" role="img" aria-label="${label}"><title>${label} by NYC pickup date</title><defs><linearGradient id="demand-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#8fba65" stop-opacity=".35"/><stop offset="100%" stop-color="#8fba65" stop-opacity=".03"/></linearGradient></defs>${grid}<path d="${path} L${x(rows.length - 1)},220 L47,220Z" fill="url(#demand-fill)"/><path d="${path}" fill="none" stroke="#287650" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>${rows.map((r, i) => `<circle class="chart-point" tabindex="0" role="img" aria-label="${esc(r.date)}: ${values[i]} ${cumulative ? 'cumulative' : 'observed'} trips" data-chart-date="${esc(r.date)}" data-chart-trips="${values[i]}" cx="${x(i)}" cy="${y(values[i])}" r="3" fill="#fff" stroke="#287650" stroke-width="1.6"><title>${esc(r.date)} · ${fmt(values[i])} trips</title></circle>`).join('')}${[...new Set([0, Math.floor((rows.length - 1) / 3), Math.floor((2 * (rows.length - 1)) / 3), rows.length - 1])].map((i) => `<text x="${x(i)}" y="248" text-anchor="${i === 0 ? 'start' : i === rows.length - 1 ? 'end' : 'middle'}">${dateLabel(rows[i].date)}</text>`).join('')}</svg><div class="chart-caption"><span class="chart-legend"><i></i>${cumulative ? 'CUMULATIVE' : 'OBSERVED'} TRIPS · NYC LOCAL DATE</span><span>Hover or tab to inspect · ${rows.length} days</span></div></div>`;
}
function bindTrend(rows) {
    document.querySelectorAll('[data-chart-mode]').forEach((button) => button.addEventListener('click', () => {
        button.closest('.trend-visual').outerHTML = line(rows, button.dataset.chartMode === 'cumulative');
        bindTrend(rows);
        document
            .querySelector(`[data-chart-mode="${button.dataset.chartMode}"]`)
            ?.focus();
    }));
    document.querySelectorAll('[data-chart-date]').forEach((point) => {
        const inspect = () => {
            const readout = point.closest('.trend-visual').querySelector('.chart-readout');
            const cumulative = point
                .closest('.trend-visual')
                .querySelector('[data-chart-mode="cumulative"]')
                ?.getAttribute('aria-pressed') === 'true';
            readout.innerHTML = `<strong>${fmt(Number(point.dataset.chartTrips))} trips</strong> · ${dateLabel(point.dataset.chartDate)}${cumulative ? ' · cumulative' : ''}`;
        };
        point.addEventListener('pointerenter', inspect);
        point.addEventListener('focus', inspect);
    });
}
function observations(trends, zones, hours) {
    const peak = trends.reduce((best, r) => (!best || r.observed_trips > best.observed_trips ? r : best), null);
    const hour = hours.reduce((best, r) => (!best || r.observed_trips > best.observed_trips ? r : best), null);
    return `<div class="overview-notes" aria-label="Observed highlights">${[
        [
            'Busiest observed day',
            peak && peak.observed_trips ? dateLabel(peak.date) : 'No observations',
            peak ? fmt(peak.observed_trips) + ' trips in this view' : 'Try a different window',
        ],
        [
            'Leading pickup zone',
            zones[0]?.zone_name ?? 'No observations',
            zones[0]
                ? zones[0].borough + ' · ' + fmt(zones[0].observed_trips) + ' trips'
                : 'Try a different zone',
        ],
        [
            'Peak pickup hour',
            hour && hour.observed_trips
                ? String(hour.hour).padStart(2, '0') +
                    ':00–' +
                    String((hour.hour + 1) % 24).padStart(2, '0') +
                    ':00'
                : 'No observations',
            'NYC local time · selected dates combined',
        ],
    ]
        .map(([label, value, note]) => `<article class="insight-card"><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`)
        .join('')}</div>`;
}
function bars(rows, unit) {
    if (!rows.length)
        return empty();
    const max = Math.max(...rows.map((r) => r.value), 1);
    return rows
        .map((r, i) => `<div class="rank-row"><span class="rank-number">${String(i + 1).padStart(2, '0')}</span><div class="rank-copy"><strong>${esc(r.label)}</strong><div class="rank-track"><i style="width:${(r.value / max) * 100}%"></i></div></div><b>${fmt(r.value)}<small> ${esc(unit)}</small></b></div>`)
        .join('');
}
function table(headers, rows) {
    return rows.length
        ? `<div class="table-wrap"><table><thead><tr>${headers.map((h) => `<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`
        : empty('No records for this view.');
}
const status = (s) => `<span class="status ${esc(s)}">${esc(s)}</span>`;
function zoneTable(zones) {
    return table(['Pickup zone / borough', 'Trips observed', 'Mean fare', 'Mean distance', 'Mean duration'], zones.map((z) => [
        `<a href="#demand" data-zone="${z.zone_id}">${esc(z.zone_name)} ↗</a><br><small>${esc(z.borough)} · TLC ${z.zone_id}</small>`,
        fmt(z.observed_trips),
        money(z.average_fare_usd),
        fmt(z.average_distance_miles, 2) + ' mi',
        fmt(z.average_duration_minutes, 1) + ' min',
    ]));
}
function context() {
    return `<div class="context-band"><div><strong>Observed, not extrapolated.</strong><p>This deterministic sample represents accepted yellow-taxi records. Counts are not expanded to all trips or city-wide mobility. Equal monthly sample caps are not evidence of equal city-wide demand.</p></div><div><strong>Place has a definition.</strong><p>Pickup/dropoff zones come from the official TLC lookup. Unknown locations remain explicitly labeled.</p></div><div><strong>A batch perspective.</strong><p>Source files publish monthly, typically two months later. Refresh time and source coverage measure different things.</p></div></div>`;
}
function scatter(rows) {
    const points = rows.filter((r) => r.temp_c !== null);
    if (!points.length)
        return empty('No matched NOAA weather observations.');
    const min = Math.min(...points.map((p) => p.temp_c)) - 2, max = Math.max(...points.map((p) => p.temp_c)) + 2, high = Math.max(...points.map((p) => p.observed_trips)) * 1.1;
    return `<svg class="chart" viewBox="0 0 700 260" role="img" aria-label="Weather and observed demand scatter plot"><title>Each point is one UTC weather reporting date. Temperature in Celsius, trips observed on vertical axis.</title><line class="grid" x1="45" x2="665" y1="220" y2="220"/>${points.map((p) => `<circle class="chart-point" tabindex="0" role="img" aria-label="${esc(p.date)}, ${fmt(p.temp_c, 1)} degrees Celsius, ${p.observed_trips} trips" cx="${45 + ((p.temp_c - min) / (max - min)) * 620}" cy="${220 - (p.observed_trips / high) * 190}" r="6" fill="${(p.precipitation_mm ?? 0) >= 1 ? '#b79b51' : '#5d8c79'}" fill-opacity=".8"><title>${esc(p.date)} · ${fmt(p.temp_c, 1)} °C · ${fmt(p.observed_trips)} trips</title></circle>`).join('')}<text x="45" y="248">${fmt(min, 1)} °C</text><text x="665" y="248" text-anchor="end">${fmt(max, 1)} °C</text><text x="8" y="28">${fmt(high)}</text><text x="17" y="220">0</text></svg><div class="chart-caption"><span>TEAL: &lt;1 mm · GOLD: ≥1 mm PRECIPITATION</span><span>NOAA LAGUARDIA / UTC REPORTING DAY</span></div>`;
}
function pagination(length) {
    return `<div class="pagination"><button id="previous" ${offset === 0 ? 'disabled' : ''}>← Previous</button><span>Rows ${length ? offset + 1 : 0}–${offset + length}</span><button id="next" ${length < 20 ? 'disabled' : ''}>Next →</button></div>`;
}
function methods() {
    return `<div class="method-grid">${[
        [
            'The observation boundary',
            'Official TLC Yellow taxi records, with a reproducible bottom-k MD5 payload sample of each monthly Parquet file. No sampling weight is applied. Invalid/refund/negative-amount records, trips outside the month, journeys over six hours and unknown lookup keys are quarantined. These exclusions can change the observed distribution.',
        ],
        [
            'Fares, not revenue',
            'Fare amount is the observed base fare in USD. It is not total company revenue, driver take-home income, profit, or a measure of the whole NYC economy. Credit-card tips exclude cash tips. The sample covers one service type and selected dates.',
        ],
        [
            'Time and weather',
            'TLC timestamps are treated as America/New_York wall clock. Daily/hourly demand uses that local clock. The weather join derives a UTC date from pickup time and matches one NOAA GSOD LaGuardia reporting day. Daily station weather is a city-level proxy, not hourly or neighborhood weather. Ambiguous fall-back timestamps use PostgreSQL’s standard-time interpretation; the January demo avoids DST.',
        ],
        [
            'Idempotency and revisions',
            'No stable trip ID is supplied. A payload MD5 fingerprint collapses exact duplicate rows; distinct legitimate trips with identical payloads cannot be distinguished, and hash collisions are theoretically possible. A transaction and partition advisory lock replace the monthly raw partition. Incremental dbt refreshes changed partitions by run ID; removed or revised rows do not linger.',
        ],
        [
            'Unusual demand, carefully',
            'For each zone/date, compare the observed count with the median of prior same-weekday dates in the preceding 56 days. Require at least three prior dates. Score = deviation / max(1.4826 × MAD, 2 trips). Flag |score| ≥3.5 and volume ≥10. A short single-month sample has a weak baseline; flags are prompts to investigate, not confirmed incidents.',
        ],
        [
            'Refresh versus recency',
            'Loaded-at timestamps describe warehouse processing freshness. Pickup-date coverage describes the historical dataset. A recent run of old data is not a fresh mobility feed. TLC files normally arrive about two months after the observed month. NOAA GSOD archive coverage is checked per date; modern backfills may require its successor dataset.',
        ],
        [
            'Weather is association',
            'Traffic, holiday schedules, service availability and selection effects can confound weather comparisons. Temperature/precipitation plots do not identify causal effects. UTC weather days at local-date filter edges are partial. Missing NOAA values remain unknown, not zero.',
        ],
        [
            'Calendar and geographic context',
            'Federal observed holidays are generated using pinned python-holidays rules, with the reference OPM calendar documented. This excludes many NYC school, local, religious and business closures. Zone names/boroughs come from the official TLC lookup, not invented coordinates. <a class="inline-link" href="https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page" target="_blank" rel="noopener">Official TLC zone maps ↗</a>',
        ],
    ]
        .map(([title, body]) => `<article class="panel"><h2>${title}</h2><p>${body}</p></article>`)
        .join('')}</div>`;
}
async function render() {
    const request = ++version;
    const page = location.hash.slice(1) || 'overview';
    currentPage = pageInfo[page] ? page : 'overview';
    const info = pageInfo[currentPage];
    $('eyebrow').textContent = info[0];
    $('title').textContent = info[1];
    $('subtitle').textContent = info[2];
    $('breadcrumb').textContent = info[3];
    document.title = `${info[3]} · AtlasIQ`;
    document.querySelectorAll('nav a').forEach((link) => {
        const active = link.getAttribute('href') === '#' + currentPage;
        link.classList.toggle('active', active);
        if (active)
            link.setAttribute('aria-current', 'page');
        else
            link.removeAttribute('aria-current');
    });
    $('view').setAttribute('aria-busy', 'true');
    $('action-status').textContent = '';
    $('filters').hidden = ['quality', 'runs', 'methodology'].includes(currentPage);
    $('export').hidden = ['quality', 'runs', 'methodology'].includes(currentPage);
    document.querySelector('.range-presets').hidden = [
        'quality',
        'runs',
        'methodology',
    ].includes(currentPage);
    let trendRows = [];
    try {
        let html = '';
        const p = params();
        if (currentPage === 'methodology')
            html = methods();
        else if (currentPage === 'quality') {
            const rows = await api('quality', new URLSearchParams({ limit: '20', offset: String(offset) }));
            html =
                panel('Quality is inspectable.', 'Pass/fail thresholds and warnings come from executed checks.', table(['Check', 'Status', 'Observed', 'Threshold', 'Checked (UTC)'], rows.map((r) => [
                    esc(r.check_name.replaceAll('_', ' ')),
                    status(r.status),
                    fmt(r.observed, 4),
                    esc(r.threshold),
                    esc(new Date(r.checked_at).toISOString().slice(0, 16).replace('T', ' ')),
                ])) + pagination(rows.length), 'ACTUAL CHECK RESULTS') + context();
        }
        else if (currentPage === 'runs') {
            const rows = await api('runs', new URLSearchParams({ limit: '20', offset: String(offset) }));
            html =
                panel('The refresh ledger.', 'Each run retains its outcome, partition, source volume and accepted sample.', table([
                    'Month / run',
                    'Status',
                    'Accepted / selected',
                    'Rejected',
                    'Runtime',
                    'Started (UTC)',
                ], rows.map((r) => [
                    esc(r.partition_month.slice(0, 7)) +
                        '<br><small>' +
                        esc(r.id.slice(0, 8)) +
                        '</small>',
                    status(r.status),
                    fmt(r.accepted_rows) + ' / ' + fmt(r.selected_rows),
                    fmt(r.rejected_rows),
                    fmt(r.elapsed_seconds, 2) + ' s',
                    esc(new Date(r.started_at).toISOString().slice(0, 16).replace('T', ' ')),
                ])) + pagination(rows.length), 'AUDITED / NO SIMULATION') + context();
        }
        else if (currentPage === 'weather') {
            const rows = await api('weather', p);
            const wet = rows.filter((r) => r.precipitation_mm !== null && r.precipitation_mm >= 1), dry = rows.filter((r) => r.precipitation_mm !== null && r.precipitation_mm < 1);
            const average = (r) => r.length ? r.reduce((s, x) => s + x.observed_trips, 0) / r.length : null;
            html =
                `<div class="two-col">${panel('Conditions, alongside demand.', 'Daily weather proxy and observed trips; tab to inspect each point.', scatter(rows), 'DESCRIPTIVE ONLY')}${panel('A comparison, not a conclusion.', 'Mean trips per matched reporting day in this view.', table(['Condition', 'Days', 'Mean observed trips'], [
                    ['Wet · ≥1 mm', fmt(wet.length), fmt(average(wet), 1)],
                    ['Dry · <1 mm', fmt(dry.length), fmt(average(dry), 1)],
                    [
                        'Unknown precipitation',
                        fmt(rows.filter((r) => r.precipitation_mm === null).length),
                        'Not imputed',
                    ],
                ]))}</div>` +
                    panel('The matched days.', 'Source NOAA station observations; units converted explicitly.', table([
                        'UTC reporting date',
                        'Temperature',
                        'Precipitation',
                        'Observed trips',
                        'Mean duration',
                    ], rows.map((r) => [
                        esc(r.date),
                        fmt(r.temp_c, 1) + ' °C',
                        fmt(r.precipitation_mm, 1) + ' mm',
                        fmt(r.observed_trips),
                        fmt(r.average_duration_minutes, 1) + ' min',
                    ]))) +
                    context();
        }
        else {
            const [s, trends, zones, hours] = await Promise.all([
                api('summary', p),
                api('trends', p),
                api('zones', currentPage === 'zones' ? params(false) : p),
                api('hourly', p),
            ]);
            trendRows = trends;
            html = kpis(s);
            if (currentPage === 'overview')
                html +=
                    `<div class="two-col">${panel('Demand over time', 'Daily pickup volume across the selected sample.', line(trends), 'DAILY / NYC LOCAL')}${panel('Where journeys begin', 'Leading pickup zones · selected sample', bars(zones.slice(0, 5).map((z) => ({ label: z.zone_name, value: z.observed_trips })), '') + `<a href="#zones" class="inline-link">Compare pickup zones <span>↗</span></a>`, 'TOP 5')}</div>` +
                        observations(trends, zones, hours) +
                        panel('The neighborhood view', 'A closer look at the top pickup zones. Select a place to explore its demand.', zoneTable(zones.slice(0, 8)));
            else if (currentPage === 'demand') {
                const anomalies = await api('anomalies', p);
                html +=
                    panel('A daily perspective.', 'Observed counts in the selected sample; no population extrapolation.', line(trends)) +
                        `<div class="two-col">${panel('Around the clock.', 'Local pickup hour, summed across dates in the filter.', bars(hours.map((h) => ({
                            label: String(h.hour).padStart(2, '0') + ':00',
                            value: h.observed_trips,
                        })), ''), 'NYC WALL CLOCK')}${panel('Worth a closer look.', 'Exploratory same-weekday median/MAD flags; short history limits confidence.', table(['Date / zone', 'Observed', 'Baseline', 'Score'], anomalies
                            .slice(0, 12)
                            .map((a) => [
                            esc(a.date) + '<br>' + esc(a.zone_name),
                            fmt(a.observed_trips),
                            fmt(a.median_trips, 1),
                            fmt(a.robust_score, 2),
                        ])), 'NOT CONFIRMED INCIDENTS')}</div>`;
            }
            else if (currentPage === 'zones') {
                const options = zones
                    .map((z) => `<option value="${z.zone_id}">${esc(z.zone_name)} / ${esc(z.borough)}</option>`)
                    .join('');
                html +=
                    panel('Put two places side by side.', 'Comparison uses the selected dates and explicit zones below.', `<form id="compare-form" class="filters"><label>First zone<select id="compare-a">${options}</select></label><label>Second zone<select id="compare-b">${options}</select></label><button class="primary" type="submit">Compare zones ↔</button></form><div id="comparison" style="margin-top:20px"></div>`) +
                        panel('The zone ledger.', 'Top 25 zones for the selected dates; individual drilldowns retain geographic context.', zoneTable(zones)) +
                        context();
            }
        }
        if (request !== version)
            return;
        $('view').innerHTML = html;
        if (['overview', 'demand', 'zones', 'weather'].includes(currentPage))
            appliedFilters = new URLSearchParams(p);
        if (trendRows.length)
            bindTrend(trendRows);
        syncPresets();
        document.querySelectorAll('[data-zone]').forEach((link) => link.addEventListener('click', () => {
            $('zone').value = link.dataset.zone;
        }));
        for (const [id, step] of [
            ['previous', -20],
            ['next', 20],
        ])
            document.getElementById(id)?.addEventListener('click', () => {
                offset = Math.max(0, offset + step);
                void render();
            });
        const compare = document.getElementById('compare-form');
        if (compare) {
            const b = $('compare-b');
            if (b.options.length > 1)
                b.selectedIndex = 1;
            const compareZones = async () => {
                try {
                    const a = $('compare-a').value, b = $('compare-b').value;
                    const x = params(false), y = params(false);
                    x.set('zone', a);
                    y.set('zone', b);
                    const [first, second] = await Promise.all([
                        api('summary', x),
                        api('summary', y),
                    ]);
                    $('comparison').innerHTML = table([
                        'Measure',
                        esc($('compare-a').selectedOptions[0]?.text),
                        esc($('compare-b').selectedOptions[0]?.text),
                    ], [
                        ['Trips observed', fmt(first.observed_trips), fmt(second.observed_trips)],
                        ['Average fare', money(first.average_fare_usd), money(second.average_fare_usd)],
                        [
                            'Average duration',
                            fmt(first.average_duration_minutes, 1) + ' min',
                            fmt(second.average_duration_minutes, 1) + ' min',
                        ],
                        [
                            'Average distance',
                            fmt(first.average_distance_miles, 2) + ' mi',
                            fmt(second.average_distance_miles, 2) + ' mi',
                        ],
                    ]);
                }
                catch (e) {
                    $('comparison').textContent = e instanceof Error ? e.message : 'Comparison unavailable';
                }
            };
            compare.addEventListener('submit', (event) => {
                event.preventDefault();
                void compareZones();
            });
            void compareZones();
        }
    }
    catch (error) {
        if (request === version) {
            $('view').innerHTML =
                `<div class="error"><strong>This view couldn’t be loaded.</strong><p>${esc(error instanceof Error ? error.message : 'Unknown error')}</p><button id="retry">Try again</button></div>`;
            $('retry').addEventListener('click', () => void render());
        }
    }
    finally {
        if (request === version)
            $('view').setAttribute('aria-busy', 'false');
    }
}
function syncPresets() {
    if (!meta)
        return;
    const end = $('end').value;
    const start = $('start').value;
    const week = new Date((meta.coverage.end ?? end) + 'T12:00:00Z');
    week.setUTCDate(week.getUTCDate() - 6);
    const weekStart = [meta.coverage.start ?? '', week.toISOString().slice(0, 10)].sort().at(-1);
    for (const [id, active] of [
        ['full-range', start === meta.coverage.start && end === meta.coverage.end],
        ['last-week', start === weekStart && end === meta.coverage.end],
    ]) {
        $(id).setAttribute('aria-pressed', String(active));
        $(id).classList.toggle('selected', active);
    }
}
async function exportDaily() {
    const button = $('export');
    button.disabled = true;
    $('action-status').textContent = 'Preparing observed daily data…';
    try {
        const p = appliedFilters ? new URLSearchParams(appliedFilters) : params();
        const rows = await api('trends', p);
        const csv = [
            'nyc_pickup_date,observed_sample_trips,average_base_fare_usd',
            ...rows.map((r) => `${r.date},${r.observed_trips},${r.average_fare_usd ?? ''}`),
        ].join('\r\n');
        const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
        const link = document.createElement('a');
        link.href = url;
        link.download = `atlasiq-daily-${p.get('start')}-${p.get('end')}${p.get('zone') ? '-zone-' + p.get('zone') : ''}.csv`;
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        $('action-status').textContent =
            `Exported ${rows.length} daily rows for the selected dates and pickup zone. Counts represent the accepted sample.`;
    }
    catch (error) {
        $('action-status').textContent =
            error instanceof Error ? error.message : 'Export unavailable. Try again.';
    }
    finally {
        button.disabled = false;
    }
}
async function initialize() {
    try {
        meta = await api('meta');
        const start = $('start'), end = $('end');
        start.value = meta.coverage.start ?? '2025-01-01';
        end.value = meta.coverage.end ?? '2025-01-31';
        $('zone').innerHTML =
            '<option value="">All pickup zones</option>' +
                meta.zone_options
                    .map((z) => `<option value="${z.zone_id}">${esc(z.zone_name)} / ${esc(z.borough)}</option>`)
                    .join('');
        const sourceRows = meta.partitions.reduce((s, p) => s + p.source_rows, 0);
        const last = meta.partitions
            .map((p) => p.loaded_at)
            .sort()
            .at(-1);
        $('coverage-note').textContent =
            `${fmt(meta.coverage.observed_trips)} accepted sample trips · ${fmt(sourceRows)} source records scanned · pickup coverage ${meta.coverage.start} – ${meta.coverage.end} · warehouse refreshed ${last ? new Date(last).toISOString().slice(0, 16).replace('T', ' ') + ' UTC' : 'not yet'}. No city-wide extrapolation.`;
        const coverageFormat = new Intl.DateTimeFormat('en-US', {
            month: 'short',
            year: 'numeric',
            timeZone: 'UTC',
        });
        const coverageStart = new Date((meta.coverage.start ?? '2025-01-01') + 'T12:00:00Z');
        const coverageEnd = new Date((meta.coverage.end ?? meta.coverage.start ?? '2025-01-01') + 'T12:00:00Z');
        $('dataset-label').innerHTML =
            `<i></i><strong>${esc(coverageFormat.formatRange(coverageStart, coverageEnd))}</strong><span>Yellow taxi · accepted sample · NYC</span>`;
        $('filters').addEventListener('submit', (event) => {
            event.preventDefault();
            if (start.value > end.value) {
                $('view').innerHTML = empty('Choose an end date on or after the start date.');
                return;
            }
            offset = 0;
            void render();
        });
        $('reset').addEventListener('click', () => {
            start.value = meta.coverage.start ?? '';
            end.value = meta.coverage.end ?? '';
            $('zone').value = '';
            offset = 0;
            void render();
        });
        $('export').addEventListener('click', () => void exportDaily());
        for (const id of ['full-range', 'last-week'])
            $(id).addEventListener('click', () => {
                end.value = meta.coverage.end ?? '';
                const week = new Date(end.value + 'T12:00:00Z');
                week.setUTCDate(week.getUTCDate() - 6);
                start.value =
                    id === 'full-range'
                        ? (meta.coverage.start ?? '')
                        : [meta.coverage.start ?? '', week.toISOString().slice(0, 10)].sort().at(-1);
                offset = 0;
                void render();
            });
        window.addEventListener('hashchange', () => {
            offset = 0;
            void render();
        });
        await render();
    }
    catch (error) {
        $('view').innerHTML =
            `<div class="error"><strong>Warehouse connection unavailable</strong><p>${esc(error instanceof Error ? error.message : 'Unknown error')}</p><p>Run the documented demo pipeline, then reload this page.</p></div>`;
        $('view').setAttribute('aria-busy', 'false');
    }
}
void initialize();
export {};
