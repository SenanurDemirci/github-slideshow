function leo_geo_doppler_sim(varargin)
% LEO_GEO_DOPPLER_SIM  LEO / GEO NTN bağlantı simülatörü: yörüngeler, Doppler, kapsama
%
% Hareketli kullanıcılar (UE: İHA, uçak, hızlı tren, gemi) bir LEO uydu
% düzlemi veya bir GEO uydusu tarafından servis edilir. Her UE için anlık
% elevasyon (alpha), eğik mesafe (d), Doppler (f_d), Doppler değişim hızı,
% serbest uzay yol kaybı (PL), gecikme / RTT, LEO handover'ları ve kapsama
% (footprint) analizi hesaplanır.
%
% Kullanım
%   leo_geo_doppler_sim                              % etkileşimli pencere
%   leo_geo_doppler_sim('Layer','GEO','Fc',20)       % GEO, Ka-band 20 GHz
%   leo_geo_doppler_sim('SavePng','ekran.png','T',120)          % tek kare
%   leo_geo_doppler_sim('SaveGif','sim.gif','Frames',60,'StepS',20)
%
% Seçenekler (isim-değer çiftleri)
%   'Layer'   'LEO' | 'GEO'      servis katmanı                  (varsayılan 'LEO')
%   'Fc'      taşıyıcı frekans [GHz]                             (2)
%   'HLeo'    LEO irtifası [km]                                  (600)
%   'NSat'    düzlemdeki LEO uydu sayısı                         (12)
%   'ElMin'   minimum elevasyon [derece]                         (10)
%   'GeoLon'  GEO'nun merkeze göre açısı [derece]                (35)
%   'Speed'   simülasyon hızı [x]                                (30)
%   'T'       başlangıç zamanı [s]                               (0)
%   'Frames'  çizilecek kare sayısı (Inf = pencere kapanana kadar)
%   'SavePng' tek kareyi PNG olarak kaydet
%   'SaveGif' animasyonu GIF olarak kaydet ('Frames' ve 'StepS' ile)
%   'StepS'   GIF'te her karede ilerlenen simülasyon süresi [s]  (20)
%
% Model (sadeleştirmeler)
%   - 2B, tek yörünge düzlemi, Dünya'ya sabit çerçeve (Dünya dönüşü LEO'da yok)
%   - GEO Dünya'ya göre sabit -> GEO Doppler'i sadece UE hareketinden gelir
%   - f_d = -f_c * (dr/dt) / c ,  PL = 20log10(d_km) + 20log10(f_GHz) + 92.45
%   - kapsama: lambda = acos(R_E cos(eps) / r) - eps
%
% MATLAB R2016b+ ve GNU Octave 6+ ile çalışır. Ek toolbox gerekmez.

opt = parse_options(varargin{:});
S = sim_init(opt);
S = sim_rebuild(S, false);
if opt.T > 0
    S = sim_advance(S, opt.T);
end

interactive = isempty(opt.SavePng) && isempty(opt.SaveGif);
fig = make_figure(interactive);
setappdata(fig, 'S', S);
if interactive
    build_controls(fig);
end

% --- tek kare
if ~isempty(opt.SavePng)
    draw_all(fig, S);
    drawnow;
    print(fig, '-dpng', '-r100', opt.SavePng);
    fprintf('saved %s\n', opt.SavePng);
    return;
end

% --- GIF kaydı
if ~isempty(opt.SaveGif)
    nf = opt.Frames; if isinf(nf), nf = 60; end
    for f = 1:nf
        S = sim_advance(S, opt.StepS);
        draw_all(fig, S);
        drawnow;
        im = frame2im(getframe(fig));
        if exist('OCTAVE_VERSION', 'builtin')
            im = uint8(round(double(im) / 51) * 51);   % Octave: önce 216 renge indir
            [A, map] = rgb2ind(im);
        else
            [A, map] = rgb2ind(im, 256);
        end
        if f == 1
            imwrite(A, map, opt.SaveGif, 'gif', 'LoopCount', Inf, 'DelayTime', 0.15);
        else
            imwrite(A, map, opt.SaveGif, 'gif', 'WriteMode', 'append', 'DelayTime', 0.15);
        end
    end
    fprintf('saved %s\n', opt.SaveGif);
    return;
end

% --- etkileşimli animasyon: gerçek geçen süre kadar ilerle
last = tic;
frame = 0;
while ishghandle(fig) && frame < opt.Frames
    S = getappdata(fig, 'S');
    dt = min(1, toc(last));
    last = tic;
    if S.playing
        S = sim_advance(S, dt * S.speed);
    end
    setappdata(fig, 'S', S);
    draw_all(fig, S);
    drawnow;
    frame = frame + 1;
end
end


% ======================================================================
%                              PARAMETRELER
% ======================================================================
function opt = parse_options(varargin)
opt = struct('Layer', 'LEO', 'Fc', 2, 'HLeo', 600, 'NSat', 12, 'ElMin', 10, ...
             'GeoLon', 35, 'Speed', 30, 'T', 0, 'Frames', Inf, ...
             'SavePng', '', 'SaveGif', '', 'StepS', 20);
names = fieldnames(opt);
for k = 1:2:numel(varargin)
    j = find(strcmpi(names, varargin{k}));
    if isempty(j)
        error('Unknown option: %s', varargin{k});
    end
    opt.(names{j}) = varargin{k + 1};
end
opt.Layer = upper(opt.Layer);
end

function K = consts()
% Fiziksel sabitler ve simülasyon ayarları
K.C      = 299792.458;     % ışık hızı [km/s]
K.MU     = 398600.4418;    % Dünya kütleçekim parametresi [km^3/s^2]
K.RE     = 6371.0;         % Dünya yarıçapı [km]
K.RGEO   = 42164.17;       % GEO yörünge yarıçapı [km]
K.D      = pi / 180;       % derece -> radyan
K.VW     = 20 * pi / 180;  % yerel görünümün yarı genişliği (merkez açı), ~ +-2220 km
K.HYST   = 8;              % handover histerezisi [derece]
K.SAMPLE = 2;              % geçmiş kayıt adımı [s]
K.WINDOW = 1800;           % Doppler grafiği penceresi [s] (30 dk)
K.TH0    = -6 * pi / 180;  % SAT-1'in başlangıç fazı
end

function U = ue_list()
% Kullanıcılar: h [km], v [km/h] (+ sağa, - sola), phi0 = başlangıç konumu [rad]
D = pi / 180;
U = struct( ...
    'id',    {'UAV', 'A/C', 'HST', 'SHIP'}, ...
    'name',  {'UAV', 'Aircraft', 'HST train', 'Ship'}, ...
    'h',     {0.3, 11, 0, 0}, ...
    'v',     {-200, 900, 400, 40}, ...
    'phi0',  {4.5 * D, -2.0 * D, -9.0 * D, 12.0 * D}, ...
    'color', {[0.12 0.54 0.41], [0.18 0.44 0.71], [0.82 0.44 0.17], [0.48 0.33 0.69]});
end

function C = colors()
C.serve = [0.66 0.46 0.11];  C.rise = [0.31 0.60 0.35];  C.set = [0.75 0.31 0.30];
C.idle  = [0.56 0.54 0.51];  C.nocov = [0.83 0.81 0.77]; C.earth = [0.94 0.91 0.86];
C.band  = [0.94 0.95 0.97];  C.geo = [0.18 0.44 0.71];
C.pal   = [0.79 0.58 0.17; 0.31 0.60 0.35; 0.75 0.31 0.30; 0.18 0.44 0.71; 0.48 0.33 0.69; 0.12 0.54 0.54];
C.dneg  = [0.18 0.44 0.71];  C.dmid = [0.95 0.94 0.91];  C.dpos = [0.75 0.31 0.30];
end


% ======================================================================
%                                 FİZİK
% ======================================================================
function a = wrap_view(a, VW)
% UE yerel görünümün dışına çıkınca diğer kenardan geri girsin (görsel kolaylık)
a = mod(a + VW, 2 * VW) - VW;
end

function L = link(ue, sat, fc)
% UE ile uydu(lar) arasındaki bağlantı.
% ue.p, ue.v : 2x1 (veya 2xM)  [km, km/s]     sat.p, sat.v : 2xN (veya 2xM)
C  = 299792.458;
dp = sat.p - ue.p;                                 % UE -> uydu vektörü
d  = sqrt(sum(dp .^ 2, 1));                        % eğik mesafe [km]
up = ue.p ./ sqrt(sum(ue.p .^ 2, 1));              % yerel zenit (yukarı) yönü
L.d   = d;
L.el  = asin(max(-1, min(1, sum(dp .* up, 1) ./ d))) * 180 / pi;   % elevasyon [derece]
L.rr  = sum(dp .* (sat.v - ue.v), 1) ./ d;        % mesafe değişim hızı [km/s]
L.fd  = -fc * 1e9 * L.rr / C;                      % Doppler [Hz]
L.pl  = 20 * log10(d) + 20 * log10(fc) + 92.45;    % serbest uzay yol kaybı [dB]
L.ow  = d / C * 1000;                              % tek yön gecikme [ms]
L.rtt = 2 * L.ow;                                  % gidiş-dönüş [ms]
end

function lam = footprint(r, el_deg)
% Minimum elevasyonda kapsama kenarının Dünya merkez açısı [rad]
el = el_deg * pi / 180;
lam = acos(6371.0 * cos(el) ./ r) - el;
end

function r = r_leo(S)
r = S.K.RE + S.h_leo;
end

function w = omega(S)
w = sqrt(S.K.MU / r_leo(S) ^ 3);                   % Kepler: w = sqrt(mu / r^3)
end

function st = ue_state(S, i, t)
% t skaler veya satır vektörü olabilir
u = S.U(i);
r = S.K.RE + u.h;
vs = u.v / 3600;
phi = wrap_view(u.phi0 + vs / r * t, S.K.VW);
st.phi = phi;
st.p = [r * sin(phi); r * cos(phi)];
st.v = [vs * cos(phi); -vs * sin(phi)];
end

function th = sat_theta(S, k, t)
% k: 0 tabanlı uydu indeksi (vektör olabilir)
a = S.K.TH0 + 2 * pi * k / S.n_sat + omega(S) * t;
th = atan2(sin(a), cos(a));
end

function st = sat_state(S, k, t)
th = sat_theta(S, k, t);
r = r_leo(S);
w = omega(S);
st.th = th;
st.p = [r * sin(th); r * cos(th)];
st.v = r * w * [cos(th); -sin(th)];
end

function st = geo_state(S)
th = S.geo_lon * S.K.D;
st.th = th;
st.p = S.K.RGEO * [sin(th); cos(th)];
st.v = [0; 0];
end

function st = ground_state(phi, RE)
st.phi = phi;
st.p = RE * [sin(phi); cos(phi)];
st.v = [0; 0];
end


% ======================================================================
%                              SİMÜLASYON
% ======================================================================
function S = sim_init(opt)
S.K = consts();
S.U = ue_list();
S.fc = opt.Fc;  S.h_leo = opt.HLeo;  S.n_sat = opt.NSat;  S.el_min = opt.ElMin;
S.geo_lon = opt.GeoLon;  S.layer = opt.Layer;  S.speed = opt.Speed;
S.playing = true;
S.t = 0;
end

function S = sim_rebuild(S, keep_t)
% Parametre değişince geçmişi yeniden hesapla (son 30 dk önceden doldurulur)
if keep_t, t0 = S.t; else, t0 = 0; end
n = numel(S.U);
S.h_t = zeros(0, 1);  S.h_fdL = zeros(0, n);  S.h_srv = zeros(0, n);  S.h_fdG = zeros(0, n);
S.events = struct('t', {}, 'ue', {}, 'from', {}, 'to', {});
S.srv = -ones(1, n);
S.srv_init = false(1, n);
S.t = t0 - S.K.WINDOW;
S.next_sample = S.t;
S = sim_advance(S, S.K.WINDOW);
end

function S = sim_advance(S, dt)
target = S.t + dt;
while S.next_sample <= target
    S = sim_sample(S, S.next_sample, true);
    S.next_sample = S.next_sample + S.K.SAMPLE;
end
S.t = target;
keep = S.h_t >= S.t - S.K.WINDOW;
S.h_t = S.h_t(keep);  S.h_fdL = S.h_fdL(keep, :);  S.h_srv = S.h_srv(keep, :);  S.h_fdG = S.h_fdG(keep, :);
end

function S = sim_sample(S, t, logit)
g = geo_state(S);
n = numel(S.U);
fdL = nan(1, n);  fdG = nan(1, n);
for i = 1:n
    [S, us, L] = eval_serving(S, i, t, logit);
    if S.srv(i) >= 0
        fdL(i) = L.fd(S.srv(i) + 1);
    end
    lg = link(us, g, S.fc);
    if lg.el >= S.el_min
        fdG(i) = lg.fd;
    end
end
S.h_t(end + 1, 1) = t;
S.h_fdL(end + 1, :) = fdL;
S.h_srv(end + 1, :) = S.srv;
S.h_fdG(end + 1, :) = fdG;
end

function [S, us, L] = eval_serving(S, i, t, logit)
% Servis eden uydu: en yüksek elevasyon + histerezis
us = ue_state(S, i, t);
L = link(us, sat_state(S, 0:S.n_sat - 1, t), S.fc);
vis = find(L.el >= S.el_min);
if isempty(vis)
    best = -1;
else
    [~, j] = max(L.el(vis));
    best = vis(j) - 1;
end
cur = S.srv(i);
if cur >= 0 && cur < S.n_sat && L.el(cur + 1) >= S.el_min
    % mevcut uydu batıyorsa ve yeni uydu belirgin şekilde daha yüksekse geç
    if best ~= cur && L.el(best + 1) - L.el(cur + 1) > S.K.HYST && L.rr(cur + 1) > 0
        cur = best;
    end
else
    cur = best;
end
if cur ~= S.srv(i)
    if logit && S.srv_init(i)
        ev = struct('t', t, 'ue', S.U(i).id, 'from', S.srv(i), 'to', cur);
        S.events = [ev, S.events];
        if numel(S.events) > 40
            S.events = S.events(1:40);
        end
    end
    S.srv(i) = cur;
end
S.srv_init(i) = true;
end

function cur = sim_current(S)
% Şu anki her UE için LEO ve GEO bağlantıları
g = geo_state(S);
for i = 1:numel(S.U)
    us = ue_state(S, i, S.t);
    cur(i).us = us; %#ok<AGROW>
    if S.srv(i) >= 0
        cur(i).leo = link(us, sat_state(S, S.srv(i), S.t), S.fc);
    else
        cur(i).leo = [];
    end
    cur(i).geo = link(us, g, S.fc);
end
end

function s = predict_ho(S, i)
% Servis eden uydu el_min'in altına inene kadar kalan süre [s] (yoksa NaN)
s = NaN;
k = S.srv(i);
if k < 0, return; end
ts = 5:5:1800;
L = link(ue_state(S, i, S.t + ts), sat_state(S, k, S.t + ts), S.fc);
j = find(L.el < S.el_min, 1);
if ~isempty(j), s = ts(j); end
end

function cv = coverage(S)
% Kapsama analizi: lambda = acos(R_E cos(eps) / r) - eps
cv.lam_leo = footprint(r_leo(S), S.el_min);
cv.lam_geo = footprint(S.K.RGEO, S.el_min);
cv.r_leo_km = cv.lam_leo * S.K.RE;
cv.r_geo_km = cv.lam_geo * S.K.RE;
cv.cap_leo = (1 - cos(cv.lam_leo)) / 2;          % Dünya yüzeyinin kapsanan oranı
cv.cap_geo = (1 - cos(cv.lam_geo)) / 2;
cv.pass_min = 2 * cv.lam_leo / omega(S) / 60;    % bir uydunun görünme süresi [dk]
cv.n_ratio = pi / cv.lam_leo;                    % kesintisiz kapsama: N > pi / lambda
cv.n_min = floor(cv.n_ratio) + 1;
cv.continuous = S.n_sat >= cv.n_min;
end


% ======================================================================
%                                ÇİZİM
% ======================================================================
function fig = make_figure(interactive)
pos = [40 40 1600 950];
if interactive
    vis = 'on';
    scr = get(0, 'ScreenSize');                     % küçük ekranlarda pencereyi sığdır
    if scr(3) > 100
        pos(3:4) = min(pos(3:4), round([0.95 * scr(3), 0.88 * scr(4)]));
    end
else
    vis = 'off';
end
fig = figure('Name', 'LEO / GEO NTN Doppler Simulator', 'NumberTitle', 'off', 'Color', 'w', ...
             'Units', 'pixels', 'Position', pos, 'Visible', vis);
if interactive, b = 0.12; else, b = 0.06; end      % alt boşluk (kontroller için)
top = 0.47;                                         % alt panellerin üst kenarı
ax.local = axes('Parent', fig, 'Position', [0.045 0.585 0.60 0.37]);
ax.orbit = axes('Parent', fig, 'Position', [0.03 b 0.25 top - b]);
ax.dop   = axes('Parent', fig, 'Position', [0.33 b + 0.12 0.32 top - b - 0.12]);
ax.cov   = axes('Parent', fig, 'Position', [0.33 b 0.32 0.08]);
ax.info  = axes('Parent', fig, 'Position', [0.68 b 0.31 0.95 - b]);
setappdata(fig, 'ax', ax);
end

function draw_all(fig, S)
ax = getappdata(fig, 'ax');
cur = sim_current(S);
draw_local(ax.local, S, cur);
draw_orbit(ax.orbit, S, cur);
draw_doppler(ax.dop, ax.cov, S);
draw_info(ax.info, S, cur);
end

function c = lighten(c, f)
c = c + (1 - c) * f;
end

function c = dop_color(f)
C = colors();
f = max(-1, min(1, f));
if f < 0
    c = C.dmid + (C.dneg - C.dmid) * (-f);
else
    c = C.dmid + (C.dpos - C.dmid) * f;
end
end

function s = fmt_hz(f)
if f < 0, sg = '-'; else, sg = '+'; end
if abs(f) >= 1000
    s = sprintf('%s%.1f kHz', sg, abs(f) / 1000);
else
    s = sprintf('%s%.0f Hz', sg, abs(f));
end
end

function s = fmt_t(t)
if t < 0, sg = '-'; else, sg = ''; end
t = round(abs(t));
s = sprintf('%s%02d:%02d', sg, floor(t / 60), mod(t, 60));
end

function s = sat_name(k)
if k < 0, s = '-'; else, s = sprintf('SAT-%d', k + 1); end
end

function [st, c] = sat_status(S, k)
C = colors();
if any(S.srv == k)
    st = 'serving'; c = C.serve;
elseif sat_theta(S, k, S.t) < 0
    st = 'rising'; c = C.rise;
else
    st = 'setting'; c = C.set;
end
end

% --- yerel bağlantı görünümü (yandan; irtifa ekseni logaritmik)
function draw_local(ax, S, cur)
K = S.K;  C = colors();  t = S.t;  VW = K.VW;  RE = K.RE;
DEG = deg_sym();
cla(ax); hold(ax, 'on');
X = @(phi) phi * RE;                                            % yer izi [km]
Y = @(phi, h) log10(1 + max(h, 0)) - 0.35 * (phi / VW) .^ 2;    % log irtifa + eğrilik
phis = linspace(-VW, VW, 200);
geo_only = strcmp(S.layer, 'GEO');
ref = ground_state(0, RE);
g = geo_state(S);

% atmosfer katmanları ve Dünya
fill_band(ax, X(phis), Y(phis, 0), Y(phis, 15), C.band);
fill_band(ax, X(phis), Y(phis, 60), Y(phis, 1000), C.band);
text(ax, X(-VW) + 40, Y(-VW, 1.3), 'troposphere', 'FontSize', 7, 'Color', [0.45 0.45 0.45]);
text(ax, X(-VW) + 40, Y(-VW, 160), 'ionosphere', 'FontSize', 7, 'Color', [0.45 0.45 0.45]);
fill_band(ax, X(phis), -ones(size(phis)), Y(phis, 0), C.earth);
plot(ax, X(phis), Y(phis, 0), 'Color', [0.25 0.25 0.25], 'LineWidth', 1.2);
text(ax, X(-VW) + 40, -0.62, sprintf('Earth surface  R_E = %.0f km', RE), 'FontSize', 7, 'Color', [0.45 0.45 0.45]);

% LEO yörüngesi
if ~geo_only
    plot(ax, X(phis), Y(phis, S.h_leo), '--', 'Color', [0.6 0.6 0.6]);
    text(ax, X(-VW) + 40, Y(-VW, S.h_leo) - 0.17, sprintf('LEO orbit  h = %.0f km,  v = %.2f km/s \\rightarrow', ...
         S.h_leo, r_leo(S) * omega(S)), 'FontSize', 7, 'Color', [0.45 0.45 0.45]);
end

% zemin Doppler şeridi: yerde sabit bir terminalin gördüğü Doppler (en iyi LEO uydusu)
fref = S.fc * 1e9 * omega(S) * RE / K.C;
seg = linspace(-VW, VW, 161);
nseg = numel(seg) - 1;
V = zeros(4 * nseg, 2);  CD = zeros(nseg, 3);
allsats = sat_state(S, 0:S.n_sat - 1, t);
for j = 1:nseg
    a = seg(j);  b = seg(j + 1);
    gt = ground_state((a + b) / 2, RE);
    col = C.nocov;
    if ~geo_only
        L = link(gt, allsats, S.fc);
        el = L.el;  el(el < S.el_min) = -Inf;
        [emax, jj] = max(el);
        if isfinite(emax), col = dop_color(L.fd(jj) / fref); end
    else
        lg = link(gt, g, S.fc);
        if lg.el >= S.el_min, col = dop_color(0); end
    end
    V(4 * j - 3:4 * j, :) = [X(a) Y(a, 0) - 0.04; X(b) Y(b, 0) - 0.04; X(b) Y(b, 0) - 0.15; X(a) Y(a, 0) - 0.15];
    CD(j, :) = col;
end
patch('Parent', ax, 'Faces', reshape(1:4 * nseg, 4, []).', 'Vertices', V, 'FaceVertexCData', CD, ...
      'FaceColor', 'flat', 'EdgeColor', 'none');

% LEO uyduları: kapsama alanı, yörünge izi, ISL, etiket
lam = footprint(r_leo(S), S.el_min);
if geo_only
    vis = [];
else
    ths = sat_theta(S, 0:S.n_sat - 1, t);
    vis = find(abs(ths) < VW * 1.1) - 1;
    [~, o] = sort(ths(vis + 1));
    vis = vis(o);
end
for q = 1:numel(vis) - 1
    ta = sat_theta(S, vis(q), t);  tb = sat_theta(S, vis(q + 1), t);
    if tb - ta < 4 * pi / S.n_sat
        plot(ax, [X(ta) X(tb)], [Y(ta, S.h_leo) Y(tb, S.h_leo)], 'Color', C.idle);
        text(ax, (X(ta) + X(tb)) / 2, (Y(ta, S.h_leo) + Y(tb, S.h_leo)) / 2 + 0.05, ...
             sprintf('ISL %.0f km', 2 * r_leo(S) * sin(pi / S.n_sat)), 'FontSize', 6, ...
             'Color', [0.45 0.45 0.45], 'HorizontalAlignment', 'center');
    end
end
for k = vis
    th = sat_theta(S, k, t);
    [st, col] = sat_status(S, k);
    serving = strcmp(st, 'serving');
    fp = linspace(max(-VW, th - lam), min(VW, th + lam), 40);
    if serving
        plot(ax, X(fp), Y(fp, 0) + 0.03, 'Color', col, 'LineWidth', 3);
        for e = [th - lam, th + lam]
            plot(ax, [X(th) X(e)], [Y(th, S.h_leo) Y(e, 0)], ':', 'Color', col);
        end
    else
        plot(ax, X(fp), Y(fp, 0) + 0.03, 'Color', lighten(col, 0.5), 'LineWidth', 2);
    end
    tr = th - omega(S) * linspace(240, 0, 25);                   % geçmiş 4 dk yörünge izi
    plot(ax, X(tr), Y(tr, S.h_leo), 'Color', col, 'LineWidth', 2);
    plot(ax, X(th), Y(th, S.h_leo), 's', 'MarkerSize', 8 + 2 * serving, 'MarkerFaceColor', col, 'MarkerEdgeColor', 'k');
    lr = link(ref, sat_state(S, k, t), S.fc);
    text(ax, X(th), Y(th, S.h_leo) + 0.13, sprintf('%s  \\alpha_{ref} %.1f%s  %s', sat_name(k), lr.el, DEG, st), ...
         'FontSize', 7, 'Color', col, 'HorizontalAlignment', 'center');
end

% GEO (ölçek dışı, üstte)
gx = X(max(-VW * 0.9, min(VW * 0.9, g.th)));
gy = 3.55;
if geo_only, gcol = C.serve; else, gcol = C.idle; end
plot(ax, gx, gy, 's', 'MarkerSize', 9, 'MarkerFaceColor', gcol, 'MarkerEdgeColor', 'k');
lg0 = link(ref, g, S.fc);
if gx > 0, ha = 'right'; dx = -60; else, ha = 'left'; dx = 60; end
text(ax, gx + dx, gy, sprintf('GEO  35 786 km (off-scale)  \\alpha_{ref} %.1f%s', lg0.el, DEG), ...
     'FontSize', 7, 'Color', gcol, 'HorizontalAlignment', ha);

% UE'ler: iz, yön oku, bağlantı çizgileri, etiketler
for i = 1:numel(S.U)
    u = S.U(i);  c = u.color;  phi = cur(i).us.phi;
    ux = X(phi);  uy = Y(phi, u.h);
    w = (u.v / 3600) / (RE + u.h);
    past = wrap_view(u.phi0 + w * (t - (1800:-20:0)), VW);       % geçmiş 30 dk iz
    xs = X(past);  xs([false, abs(diff(past)) > VW]) = NaN;
    plot(ax, xs, Y(past, u.h), ':', 'Color', c, 'LineWidth', 1.3);
    pf = phi + w * 600;                                          % gelecek 10 dk yön
    plot(ax, [ux X(pf)], [uy Y(pf, u.h)], '--', 'Color', c);
    if u.v >= 0, mk = '>'; else, mk = '<'; end
    plot(ax, X(pf), Y(pf, u.h), mk, 'MarkerSize', 4, 'MarkerFaceColor', c, 'MarkerEdgeColor', c);
    % bağlantılar
    if S.srv(i) >= 0 && ~geo_only
        th = sat_theta(S, S.srv(i), t);
        plot(ax, [ux X(th)], [uy Y(th, S.h_leo)], '-', 'Color', c, 'LineWidth', 1.5);
        text(ax, ux + (X(th) - ux) * 0.6, uy + (Y(th, S.h_leo) - uy) * 0.6, sprintf(' d=%.0f km', cur(i).leo.d), ...
             'FontSize', 6, 'Color', c);
    end
    if cur(i).geo.el >= S.el_min
        if geo_only
            plot(ax, [ux gx], [uy gy], '-', 'Color', c, 'LineWidth', 1.3);
            text(ax, ux + (gx - ux) * 0.35, uy + (gy - uy) * 0.35, sprintf(' d=%.0f km', cur(i).geo.d), ...
                 'FontSize', 6, 'Color', c);
        else
            plot(ax, [ux gx], [uy gy], ':', 'Color', lighten(c, 0.6));
        end
    end
    if u.h > 0.1
        plot(ax, [ux ux], [uy Y(phi, 0)], 'Color', lighten(c, 0.6));
    end
    plot(ax, ux, uy, mk, 'MarkerSize', 9, 'MarkerFaceColor', c, 'MarkerEdgeColor', 'k');
    if geo_only
        if cur(i).geo.el >= S.el_min, L = cur(i).geo; else, L = []; end
    else
        L = cur(i).leo;
    end
    if u.v >= 0, arr = '\rightarrow'; else, arr = '\leftarrow'; end
    lines = {sprintf('%s  %d km/h %s', u.name, abs(u.v), arr)};
    if isempty(L)
        lines{end + 1} = 'no coverage';
    else
        lines{end + 1} = sprintf('\\alpha %.1f%s   f_d %s', L.el, DEG, fmt_hz(L.fd));
        lines{end + 1} = sprintf('d %.0f km   RTT %.1f ms', L.d, L.rtt);
    end
    text(ax, ux, uy + 0.22 + 0.12 * mod(i - 1, 2), lines, 'FontSize', 7, 'Color', c, ...
         'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom', 'BackgroundColor', 'w', 'Margin', 1);
end

xlim(ax, [X(-VW) X(VW)]);
ylim(ax, [-0.75 3.75]);
set(ax, 'YTick', log10(1 + [0 1 10 100 1000]), 'YTickLabel', {'0', '1 km', '10 km', '100 km', '1000 km'}, ...
        'FontSize', 8, 'Box', 'on', 'Layer', 'top');
xlabel(ax, 'ground track [km]   (altitude axis is logarithmic; angles, ranges & Doppler are true geometry)', 'FontSize', 8);
if geo_only
    extra = sprintf('GEO @ %+.0f%s', S.geo_lon, DEG);
else
    sv = unique(S.srv(S.srv >= 0));
    names = arrayfun(@sat_name, sv, 'UniformOutput', false);
    extra = ['serving: ' strjoin(names, ', ') sprintf('   |   HO events: %d', numel(S.events))];
end
title(ax, sprintf('LOCAL LINK VIEW   |   t = %s   |   %.0fx   |   layer %s   |   %s   |   f_c %g GHz', ...
      fmt_t(t), S.speed, S.layer, extra, S.fc), 'FontSize', 10, 'FontWeight', 'normal');
hold(ax, 'off');
end

function fill_band(ax, x, ylo, yhi, col)
patch('Parent', ax, 'XData', [x fliplr(x)], 'YData', [yhi fliplr(ylo)], 'FaceColor', col, 'EdgeColor', 'none');
end

% --- yörünge görünümü (gerçek ölçek)
function draw_orbit(ax, S, cur)
K = S.K;  C = colors();  t = S.t;  RE = K.RE;  DEG = deg_sym();
cla(ax); hold(ax, 'on');
pol = @(th, r) deal(r .* sin(th), r .* cos(th));
geo_only = strcmp(S.layer, 'GEO');
full = linspace(0, 2 * pi, 361);
[x, y] = pol(full, RE);
patch('Parent', ax, 'XData', x, 'YData', y, 'FaceColor', C.earth, 'EdgeColor', [0.25 0.25 0.25]);
[x, y] = pol(linspace(-K.VW, K.VW, 40), RE);
plot(ax, x, y, 'k', 'LineWidth', 4);                             % yerel görünüm penceresi
if ~geo_only
    [x, y] = pol(full, r_leo(S));  plot(ax, x, y, '--', 'Color', [0.6 0.6 0.6]);
end
[x, y] = pol(full, K.RGEO);  plot(ax, x, y, '--', 'Color', [0.6 0.6 0.6]);
% GEO kapsama konisi
g = geo_state(S);
lg = footprint(K.RGEO, S.el_min);
if geo_only, gcol = C.serve; else, gcol = C.idle; end
[ex, ey] = pol(linspace(g.th - lg, g.th + lg, 60), RE);
patch('Parent', ax, 'XData', [g.p(1) ex], 'YData', [g.p(2) ey], 'FaceColor', gcol, 'FaceAlpha', 0.08, 'EdgeColor', 'none');
[ex, ey] = pol(linspace(g.th - lg, g.th + lg, 60), RE * 1.01);
plot(ax, ex, ey, 'Color', gcol, 'LineWidth', 3);
plot(ax, g.p(1), g.p(2), 's', 'MarkerSize', 8, 'MarkerFaceColor', gcol, 'MarkerEdgeColor', 'k');
% LEO uyduları
lam = footprint(r_leo(S), S.el_min);
if ~geo_only
    for k = 0:S.n_sat - 1
        th = sat_theta(S, k, t);
        serving = any(S.srv == k);
        if serving, c = C.serve; else, c = C.pal(mod(k, 6) + 1, :); end
        [x, y] = pol(linspace(th - omega(S) * 480, th, 30), r_leo(S));
        plot(ax, x, y, 'Color', c, 'LineWidth', 2);
        if serving
            [ex, ey] = pol(linspace(th - lam, th + lam, 40), RE);
            [sx, sy] = pol(th, r_leo(S));
            patch('Parent', ax, 'XData', [sx ex], 'YData', [sy ey], 'FaceColor', c, 'FaceAlpha', 0.15, 'EdgeColor', 'none');
            [ex, ey] = pol(linspace(th - lam, th + lam, 40), RE * 1.005);
            plot(ax, ex, ey, 'Color', c, 'LineWidth', 3);
        end
        [x, y] = pol(th, r_leo(S));
        plot(ax, x, y, 'o', 'MarkerSize', 4 + 2 * serving, 'MarkerFaceColor', c, 'MarkerEdgeColor', c);
        [x, y] = pol(th, r_leo(S) * 1.07);
        text(ax, x, y, sat_name(k), 'FontSize', 6, 'Color', c, 'HorizontalAlignment', 'center', 'Clipping', 'on');
    end
end
% UE'ler ve bağlantılar
for i = 1:numel(S.U)
    p = cur(i).us.p;
    if ~geo_only && S.srv(i) >= 0
        [qx, qy] = pol(sat_theta(S, S.srv(i), t), r_leo(S));
        plot(ax, [p(1) qx], [p(2) qy], 'Color', S.U(i).color);
    elseif geo_only && cur(i).geo.el >= S.el_min
        plot(ax, [p(1) g.p(1)], [p(2) g.p(2)], 'Color', S.U(i).color);
    end
    plot(ax, p(1), p(2), 'o', 'MarkerSize', 3, 'MarkerFaceColor', S.U(i).color, 'MarkerEdgeColor', S.U(i).color);
end
if geo_only
    R = K.RGEO * 1.12;
    xlim(ax, [-R R]);  ylim(ax, [-R * 0.75 R * 1.08]);
    ttl = {'ORBIT VIEW  (to scale, GEO)', sprintf('footprint @ %.0f%s: \\pm%.1f%s  (%.0f km)', S.el_min, DEG, lg / K.D, DEG, lg * RE)};
else
    R = r_leo(S) * 1.25;
    xlim(ax, [-R R]);  ylim(ax, [-R * 0.55 R * 1.05]);
    ttl = {'ORBIT VIEW  (to scale, LEO zoom)', sprintf('footprint @ %.0f%s: LEO \\pm%.1f%s (%.0f km), GEO \\pm%.1f%s', ...
           S.el_min, DEG, lam / K.D, DEG, lam * RE, lg / K.D, DEG)};
end
set(ax, 'DataAspectRatio', [1 1 1], 'XTick', [], 'YTick', [], 'Box', 'on');
title(ax, ttl, 'FontSize', 9, 'FontWeight', 'normal');
hold(ax, 'off');
end

% --- Doppler grafiği ve kapsama zaman çizelgesi
function draw_doppler(ax, axc, S)
C = colors();
cla(ax); cla(axc);
hold(ax, 'on');
tt = (S.h_t - S.t) / 60;                       % dakika, 0 = şimdi
geo_only = strcmp(S.layer, 'GEO');
n = numel(S.U);
h = zeros(1, n);
for i = 1:n
    c = S.U(i).color;
    if geo_only
        h(i) = plot(ax, tt, S.h_fdG(:, i) / 1e3, '-', 'Color', c, 'LineWidth', 1.6);
    else
        plot(ax, tt, S.h_fdG(:, i) / 1e3, '--', 'Color', lighten(c, 0.6));
        y = S.h_fdL(:, i);
        y([false; diff(S.h_srv(:, i)) ~= 0]) = NaN;             % handover anında çizgiyi kopar
        h(i) = plot(ax, tt, y / 1e3, '-', 'Color', c, 'LineWidth', 1.6);
    end
end
plot(ax, [-30 0], [0 0], 'Color', [0.5 0.5 0.5]);
xlim(ax, [-S.K.WINDOW / 60 0]);
ylabel(ax, 'f_d [kHz]');
set(ax, 'XTickLabel', {}, 'FontSize', 8, 'Box', 'on');
grid(ax, 'on');
if geo_only, lt = 'GEO (UE motion only)'; else, lt = 'solid: LEO serving   dashed: GEO'; end
legend(ax, h, {S.U.id}, 'Location', 'northwest', 'FontSize', 7, 'Orientation', 'horizontal');
title(ax, ['DOPPLER f_d(t)  |  last 30 min  |  ' lt], 'FontSize', 9, 'FontWeight', 'normal');
hold(ax, 'off');

% kapsama zaman çizelgesi: renk = servis eden uydu, siyah çizgi = handover
rgb = zeros(n, numel(tt), 3);
for i = 1:n
    for j = 1:numel(tt)
        if geo_only
            if isnan(S.h_fdG(j, i)), col = C.nocov; else, col = C.serve; end
        else
            k = S.h_srv(j, i);
            if k < 0, col = C.nocov; else, col = C.pal(mod(k, 6) + 1, :); end
        end
        rgb(i, j, :) = reshape(col, 1, 1, 3);
    end
end
hold(axc, 'on');
image('Parent', axc, 'XData', [tt(1) tt(end)], 'YData', [1 n], 'CData', rgb);
if ~geo_only
    for i = 1:n
        ho = tt([false; diff(S.h_srv(:, i)) ~= 0]);
        for x = ho.'
            plot(axc, [x x], [i - 0.5 i + 0.5], 'k', 'LineWidth', 1.2);
        end
    end
end
xlim(axc, [-S.K.WINDOW / 60 0]);
ylim(axc, [0.5 n + 0.5]);
set(axc, 'YDir', 'reverse', 'YTick', 1:n, 'YTickLabel', {S.U.id}, 'FontSize', 7, 'Box', 'on');
xlabel(axc, 'time relative to now [min]    (coverage: colour = serving SAT,  | = handover)', 'FontSize', 8);
hold(axc, 'off');
end

% --- sağ panel: tablolar
function draw_info(ax, S, cur)
C = colors();  DEG = deg_sym();
cla(ax); hold(ax, 'on');
set(ax, 'XLim', [0 1], 'YLim', [0 1], 'Visible', 'off');
geo_only = strcmp(S.layer, 'GEO');
n = numel(S.U);
mono = {'FontName', 'Courier', 'FontSize', 8, 'Interpreter', 'none'};

% UE başına bağlantı değerleri
L = cell(1, n);  rate = nan(1, n);
for i = 1:n
    if geo_only
        if cur(i).geo.el >= S.el_min, L{i} = cur(i).geo; end
        if ~isempty(L{i})
            l1 = link(ue_state(S, i, S.t + 1), geo_state(S), S.fc);
            rate(i) = l1.fd - L{i}.fd;
        end
    else
        L{i} = cur(i).leo;
        if ~isempty(L{i})
            l1 = link(ue_state(S, i, S.t + 1), sat_state(S, S.srv(i), S.t + 1), S.fc);
            rate(i) = l1.fd - L{i}.fd;
        end
    end
end
rows = {'v', 'h', 'sat', 'alpha', 'd', 'f_d', 'df_d/dt', 'PL', 'delay', 'RTT', 'link'};
y = 0.98;
text(ax, 0, y, sprintf('PER-UE LINK VALUES  (%s)', S.layer), 'FontWeight', 'bold', 'FontSize', 10, 'Interpreter', 'none');
y = y - 0.035;
xs = [0.0 0.27 0.47 0.67 0.87];
for i = 1:n
    text(ax, xs(i + 1), y, S.U(i).id, 'Color', S.U(i).color, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', mono{:});
end
for r = 1:numel(rows)
    y = y - 0.024;
    text(ax, xs(1), y, rows{r}, 'Color', [0.4 0.4 0.4], mono{:});
    for i = 1:n
        u = S.U(i);  l = L{i};
        switch rows{r}
            case 'v',   s = sprintf('%+d km/h', u.v);
            case 'h'
                if u.h >= 1, s = sprintf('%g km', u.h); elseif u.h > 0, s = sprintf('%.0f m', u.h * 1000); else, s = 'ground'; end
            case 'sat'
                if geo_only
                    if isempty(l), s = '-'; else, s = 'GEO'; end
                else
                    s = sat_name(S.srv(i));
                end
            otherwise
                if isempty(l)
                    s = '-';
                    if strcmp(rows{r}, 'link'), s = 'no cov.'; end
                else
                    switch rows{r}
                        case 'alpha',   s = sprintf('%.1f%s', l.el, DEG);
                        case 'd',       s = sprintf('%.0f km', l.d);
                        case 'f_d',     s = fmt_hz(l.fd);
                        case 'df_d/dt', s = sprintf('%+.1f Hz/s', rate(i));
                        case 'PL',      s = sprintf('%.1f dB', l.pl);
                        case 'delay',   s = sprintf('%.2f ms', l.ow);
                        case 'RTT',     s = sprintf('%.1f ms', l.rtt);
                        case 'link',    s = 'LOS';
                    end
                end
        end
        text(ax, xs(i + 1), y, s, 'HorizontalAlignment', 'center', mono{:});
    end
end

% takımyıldız
y = y - 0.05;
ref = ground_state(0, S.K.RE);
if geo_only, hdr = 'SATELLITE'; else, hdr = 'CONSTELLATION'; end
text(ax, 0, y, hdr, 'FontWeight', 'bold', 'FontSize', 10, 'Interpreter', 'none');
if ~geo_only
    ths = sat_theta(S, 0:S.n_sat - 1, S.t);
    ks = find(abs(ths) < S.K.VW * 1.6) - 1;
    [~, o] = sort(-ths(ks + 1));
    for k = ks(o)
        y = y - 0.022;
        [st, c] = sat_status(S, k);
        lr = link(ref, sat_state(S, k, S.t), S.fc);
        if lr.el < 0, st = 'below horizon'; end
        text(ax, 0, y, sprintf('%-6s  alpha_ref = %6.1f%s  %s', sat_name(k), lr.el, DEG, st), 'Color', c, mono{:});
    end
end
y = y - 0.022;
lg = link(ref, geo_state(S), S.fc);
if geo_only, c = C.serve; st = 'serving'; else, c = [0.45 0.45 0.45]; st = 'standby'; end
text(ax, 0, y, sprintf('%-6s  alpha_ref = %6.1f%s  %s', 'GEO', lg.el, DEG, st), 'Color', c, mono{:});
y = y - 0.03;
if geo_only
    info = sprintf('GEO h = 35 786 km, fixed relative to Earth (T = 23 h 56 min), f_c = %g GHz', S.fc);
else
    info = sprintf('LEO h = %.0f km, v = %.2f km/s, T = %.1f min, %d/plane, f_c = %g GHz', ...
                   S.h_leo, r_leo(S) * omega(S), 2 * pi / omega(S) / 60, S.n_sat, S.fc);
end
text(ax, 0, y, info, 'FontSize', 7.5, 'Color', [0.4 0.4 0.4], 'Interpreter', 'none');

% kapsama (footprint) analizi
cv = coverage(S);
y = y - 0.05;
text(ax, 0, y, 'COVERAGE', 'FontWeight', 'bold', 'FontSize', 10, 'Interpreter', 'none');
text(ax, 0.32, y, '\lambda = arccos(R_E cos\epsilon / r) - \epsilon', 'FontSize', 8, 'Color', [0.4 0.4 0.4]);
cl = {sprintf('eps_min = %.0f%s', S.el_min, DEG), [0.2 0.2 0.2]; ...
      sprintf('LEO %.0f km: lambda = %.1f%s -> radius %.0f km (%.1f%% of Earth), visible %.1f min', ...
              S.h_leo, cv.lam_leo / S.K.D, DEG, cv.r_leo_km, 100 * cv.cap_leo, cv.pass_min), [0.2 0.2 0.2]; ...
      sprintf('GEO: lambda = %.1f%s -> radius %.0f km (%.0f%% of Earth)', cv.lam_geo / S.K.D, DEG, cv.r_geo_km, ...
              100 * cv.cap_geo), [0.2 0.2 0.2]};
if ~geo_only
    if cv.continuous, msg = 'continuous'; c = C.rise; else, msg = 'COVERAGE GAPS'; c = C.set; end
    cl(end + 1, :) = {sprintf('Sats/plane needed: N > pi/lambda = %.1f -> N_min = %d, now %d -> %s', ...
                       cv.n_ratio, cv.n_min, S.n_sat, msg), c};
end
for q = 1:size(cl, 1)
    y = y - 0.022;
    text(ax, 0, y, cl{q, 1}, 'FontSize', 7.5, 'Color', cl{q, 2}, 'Interpreter', 'none');
end

% bağlantı durumu + handover kaydı
y = y - 0.05;
text(ax, 0, y, 'LINK STATE', 'FontWeight', 'bold', 'FontSize', 10, 'Interpreter', 'none');
if ~geo_only
    for i = 1:n
        y = y - 0.022;
        if S.srv(i) >= 0
            s = predict_ho(S, i);
            if isnan(s), hs = '>30:00'; else, hs = fmt_t(s); end
            msg = sprintf('%-5s %s -> HO in %s', S.U(i).id, sat_name(S.srv(i)), hs);
        else
            msg = sprintf('%-5s no LEO coverage', S.U(i).id);
        end
        text(ax, 0, y, msg, 'Color', S.U(i).color, mono{:});
    end
else
    mx = max(arrayfun(@(c) abs(c.geo.fd), cur));
    y = y - 0.022;
    text(ax, 0, y, 'GEO serving UEs in footprint, no handovers', 'FontSize', 8, 'Interpreter', 'none');
    y = y - 0.022;
    text(ax, 0, y, ['Doppler only from UE motion (max ' fmt_hz(mx) ')'], 'FontSize', 8, 'Interpreter', 'none');
end
rg = mean(arrayfun(@(c) c.geo.rtt, cur));
y = y - 0.028;
if geo_only
    s = sprintf('Mean access RTT: GEO %.1f ms', rg);
else
    rl = [];
    for i = 1:n, if ~isempty(cur(i).leo), rl(end + 1) = cur(i).leo.rtt; end, end %#ok<AGROW>
    s = sprintf('Mean access RTT: LEO %.1f ms, GEO %.1f ms', mean(rl), rg);
end
text(ax, 0, y, s, 'FontSize', 8, 'Color', [0.4 0.4 0.4], 'Interpreter', 'none');
if ~geo_only
    for q = 1:min(6, numel(S.events))
        y = y - 0.02;
        e = S.events(q);
        text(ax, 0, y, sprintf('%s  %-4s %s -> %s', fmt_t(e.t), e.ue, sat_name(e.from), sat_name(e.to)), mono{:});
    end
end
hold(ax, 'off');
end


% ======================================================================
%                            KONTROLLER (UI)
% ======================================================================
function build_controls(fig)
S = getappdata(fig, 'S');
bg = get(fig, 'Color');
mk_text = @(x, str) uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [x 0.045 0.07 0.025], ...
                              'String', str, 'BackgroundColor', bg, 'HorizontalAlignment', 'left');
% katman ve frekans
mk_text(0.03, 'Layer');
uicontrol(fig, 'Style', 'popupmenu', 'Units', 'normalized', 'Position', [0.03 0.015 0.06 0.03], ...
          'String', {'LEO', 'GEO'}, 'Value', 1 + strcmp(S.layer, 'GEO'), ...
          'Callback', @(src, evt) on_param(fig, 'layer', src));
mk_text(0.10, 'Carrier');
fcs = [1.6 2 12 20 30];
[~, jf] = min(abs(fcs - S.fc));
uicontrol(fig, 'Style', 'popupmenu', 'Units', 'normalized', 'Position', [0.10 0.015 0.08 0.03], ...
          'String', {'L 1.6 GHz', 'S 2 GHz', 'Ku 12 GHz', 'Ka 20 GHz', 'Ka 30 GHz'}, 'Value', jf, ...
          'Callback', @(src, evt) on_param(fig, 'fc', src));
% kaydırıcılar
sl = {'h_leo', 'LEO alt [km]', 400, 1500, S.h_leo; 'n_sat', 'Sats/plane', 6, 24, S.n_sat; ...
      'el_min', 'Min elev [deg]', 0, 40, S.el_min; 'geo_lon', 'GEO offset [deg]', -70, 70, S.geo_lon; ...
      'speed', 'Speed [x]', 1, 120, S.speed};
lbl = struct();
for q = 1:size(sl, 1)
    x = 0.20 + (q - 1) * 0.105;
    lbl.(sl{q, 1}) = uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [x 0.045 0.10 0.025], ...
                               'String', sprintf('%s: %g', sl{q, 2}, sl{q, 5}), 'BackgroundColor', bg, ...
                               'HorizontalAlignment', 'left');
    uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x 0.015 0.095 0.03], ...
              'Min', sl{q, 3}, 'Max', sl{q, 4}, 'Value', sl{q, 5}, ...
              'Callback', @(src, evt) on_param(fig, sl{q, 1}, src));
end
setappdata(fig, 'labels', lbl);
setappdata(fig, 'label_names', sl(:, 1:2));
% butonlar
uicontrol(fig, 'Style', 'pushbutton', 'Units', 'normalized', 'Position', [0.74 0.015 0.06 0.045], ...
          'String', 'Pause', 'Callback', @(src, evt) on_play(fig, src));
uicontrol(fig, 'Style', 'pushbutton', 'Units', 'normalized', 'Position', [0.81 0.015 0.06 0.045], ...
          'String', 'Reset', 'Callback', @(src, evt) on_reset(fig));
uicontrol(fig, 'Style', 'pushbutton', 'Units', 'normalized', 'Position', [0.88 0.015 0.09 0.045], ...
          'String', 'Coverage analysis', 'Callback', @(src, evt) on_coverage(fig));
end

function on_param(fig, name, src)
S = getappdata(fig, 'S');
switch name
    case 'layer'
        items = get(src, 'String');
        S.layer = items{get(src, 'Value')};
    case 'fc'
        fcs = [1.6 2 12 20 30];
        S.fc = fcs(get(src, 'Value'));
        S = sim_rebuild(S, true);
    case 'speed'
        S.speed = round(get(src, 'Value'));
    otherwise
        step = 1;
        if strcmp(name, 'h_leo'), step = 10; end
        S.(name) = round(get(src, 'Value') / step) * step;
        S = sim_rebuild(S, true);
end
lbl = getappdata(fig, 'labels');
names = getappdata(fig, 'label_names');
if isfield(lbl, name)
    j = find(strcmp(names(:, 1), name));
    set(lbl.(name), 'String', sprintf('%s: %g', names{j, 2}, S.(name)));
end
setappdata(fig, 'S', S);
end

function on_play(fig, src)
S = getappdata(fig, 'S');
S.playing = ~S.playing;
if S.playing, set(src, 'String', 'Pause'); else, set(src, 'String', 'Play'); end
setappdata(fig, 'S', S);
end

function on_reset(fig)
S = getappdata(fig, 'S');
S = sim_rebuild(S, false);
setappdata(fig, 'S', S);
end

function on_coverage(fig)
S = getappdata(fig, 'S');
coverage_analysis(S.h_leo, S.el_min, S.n_sat);
end

function s = deg_sym()
% Derece işareti: MATLAB karakterleri UTF-16, Octave ise UTF-8 bayt olarak tutar
if exist('OCTAVE_VERSION', 'builtin')
    s = char([194 176]);
else
    s = char(176);
end
end
