function fig = coverage_analysis(h_leo, el_min, n_sat, visible)
% COVERAGE_ANALYSIS  Kapsama (footprint) analizi figürü
%
%   lambda = acos(R_E cos(eps) / r) - eps      (Dünya merkez açısı)
%   yerdeki yarıçap = R_E * lambda
%   tek düzlemde kesintisiz kapsama:  N > pi / lambda
%
% Kullanım
%   coverage_analysis                 % 600 km, eps = 10 deg, N = 12
%   coverage_analysis(1200, 30, 12)   % farklı irtifa / min elevasyon / uydu sayısı
%   fig = coverage_analysis(600, 10, 12, 'off');  print(fig, '-dpng', 'kapsama.png')
%
% (a) kapsama yarıçapı - irtifa       (b) gereken uydu sayısı - irtifa
% (c) kapsama üçgeni (geometri)        (d) LEO ve GEO kapsaması gerçek ölçekte

if nargin < 1 || isempty(h_leo),  h_leo = 600; end
if nargin < 2 || isempty(el_min), el_min = 10; end
if nargin < 3 || isempty(n_sat),  n_sat = 12; end
if nargin < 4, visible = 'on'; end

RE = 6371.0;  RGEO = 42164.17;  D = pi / 180;  DEG = deg_sym();
serve = [0.66 0.46 0.11];  geoc = [0.18 0.44 0.71];  earth = [0.94 0.91 0.86];  uec = [0.82 0.44 0.17];
fp = @(r, e) acos(RE * cos(e * D) ./ r) - e * D;          % footprint açısı [rad]
pol = @(th, r) deal(r .* sin(th), r .* cos(th));

fig = figure('Name', 'Coverage analysis', 'NumberTitle', 'off', 'Color', 'w', ...
             'Units', 'pixels', 'Position', [60 60 1400 900], 'Visible', visible);
hs = linspace(300, 2000, 300);
eps_list = unique([0 10 30 el_min]);
cols = [0.27 0.00 0.33; 0.13 0.57 0.55; 0.55 0.80 0.25; 0.85 0.65 0.10];
lam0 = fp(RE + h_leo, el_min);
n0 = floor(pi / lam0) + 1;

% (a) kapsama yarıçapı
a = subplot(2, 2, 1); hold(a, 'on');
lg = {};
for q = 1:numel(eps_list)
    e = eps_list(q);
    lw = 1.2 + 1.2 * (e == el_min);
    plot(a, hs, fp(RE + hs, e) * RE, 'Color', cols(q, :), 'LineWidth', lw);
    lg{end + 1} = sprintf('\\epsilon = %g%s   (GEO: %.0f km)', e, DEG, fp(RGEO, e) * RE); %#ok<AGROW>
end
plot(a, h_leo, lam0 * RE, 'ko', 'MarkerFaceColor', 'k');
text(a, h_leo + 60, lam0 * RE + 350, sprintf('%g km, \\epsilon = %g%s\n\\lambda = %.1f%s  \\rightarrow  %.0f km', ...
     h_leo, el_min, DEG, lam0 / D, DEG, lam0 * RE), 'FontSize', 9);
legend(a, lg, 'Location', 'northwest', 'FontSize', 8);
xlabel(a, 'LEO altitude h [km]');
ylabel(a, 'footprint radius on ground  R_E\lambda  [km]');
title(a, '(a) Coverage radius vs altitude and min elevation', 'FontWeight', 'normal');
grid(a, 'on'); box(a, 'on');

% (b) gereken uydu sayısı
b = subplot(2, 2, 2); hold(b, 'on');
for q = 1:numel(eps_list)
    e = eps_list(q);
    lw = 1.2 + 1.2 * (e == el_min);
    stairs(b, hs, floor(pi ./ fp(RE + hs, e)) + 1, 'Color', cols(q, :), 'LineWidth', lw);
end
plot(b, [hs(1) hs(end)], [n_sat n_sat], '--', 'Color', [0.4 0.4 0.4]);
text(b, hs(end), n_sat + 0.8, sprintf('simulation: N = %d', n_sat), 'HorizontalAlignment', 'right', 'FontSize', 8);
plot(b, h_leo, n0, 'ko', 'MarkerFaceColor', 'k');
text(b, h_leo + 60, n0 + 4, sprintf('N_{min} = %d', n0), 'FontSize', 9);
legend(b, arrayfun(@(e) sprintf('\\epsilon = %g%s', e, DEG), eps_list, 'UniformOutput', false), ...
       'Location', 'northeast', 'FontSize', 8);
ylim(b, [0 40]);
xlabel(b, 'LEO altitude h [km]');
ylabel(b, 'satellites per plane  N_{min} = floor(\pi/\lambda) + 1');
title(b, '(b) Satellites needed for continuous coverage (one plane)', 'FontWeight', 'normal');
grid(b, 'on'); box(b, 'on');

% (c) kapsama üçgeni: Dünya merkezi O, kenardaki UE U, uydu S
c = subplot(2, 2, 3); hold(c, 'on');
r = RE + h_leo;
eta = asin(RE * cos(el_min * D) / r);
th = linspace(-0.45, 0.45, 300);
[x, y] = pol(th, RE);
patch('Parent', c, 'XData', [x fliplr(x)], 'YData', [y RE * 0.75 * ones(size(y))], 'FaceColor', earth, 'EdgeColor', 'none');
plot(c, x, y, 'Color', [0.25 0.25 0.25], 'LineWidth', 1.2);
[x, y] = pol(th, r);  plot(c, x, y, '--', 'Color', [0.6 0.6 0.6]);
[Sx, Sy] = pol(0, r);  [Ux, Uy] = pol(lam0, RE);  [Vx, Vy] = pol(-lam0, RE);
plot(c, [Sx Ux], [Sy Uy], 'Color', serve, 'LineWidth', 2);
plot(c, [Sx Vx], [Sy Vy], 'Color', serve, 'LineWidth', 2);
[x, y] = pol(linspace(-lam0, lam0, 80), RE * 1.002);
plot(c, x, y, 'Color', serve, 'LineWidth', 5);
plot(c, [0 0], [RE * 0.78 r], ':', 'Color', [0.4 0.4 0.4]);
plot(c, [0 Ux * 0.93], [RE * 0.78 RE * 0.78 + (Uy - RE * 0.78) * 0.93], ':', 'Color', [0.4 0.4 0.4]);
hx = [cos(lam0) -sin(lam0)];                                 % UE'nin yerel ufku
plot(c, [Ux - hx(1) * 900, Ux + hx(1) * 300], [Uy - hx(2) * 900, Uy + hx(2) * 300], 'Color', [0.5 0.5 0.5]);
plot(c, Sx, Sy, 's', 'MarkerSize', 10, 'MarkerFaceColor', serve, 'MarkerEdgeColor', 'k');
plot(c, Ux, Uy, 'o', 'MarkerSize', 7, 'MarkerFaceColor', uec, 'MarkerEdgeColor', 'k');
text(c, Sx + 60, Sy + 60, sprintf('satellite (h = %g km)', h_leo), 'FontSize', 9);
text(c, Sx + 110, Sy - 420, sprintf('\\eta = %.1f%s\n(nadir angle)', eta / D, DEG), 'FontSize', 9, 'Color', serve);
text(c, Ux + 60, Uy + 90, sprintf('\\epsilon = %g%s', el_min, DEG), 'FontSize', 10, 'Color', uec, 'FontWeight', 'bold');
text(c, Ux, Uy - 260, 'UE at coverage edge', 'FontSize', 8, 'HorizontalAlignment', 'center');
text(c, lam0 * RE * 0.25, RE * 0.82, sprintf('\\lambda = %.1f%s  (Earth-centre angle)', lam0 / D, DEG), 'FontSize', 9);
text(c, 0, RE - 200, sprintf('radius = R_E\\lambda = %.0f km', lam0 * RE), 'FontSize', 9, ...
     'HorizontalAlignment', 'center', 'Color', serve, 'FontWeight', 'bold');
set(c, 'DataAspectRatio', [1 1 1], 'XTick', [], 'YTick', [], 'Box', 'on');
xlim(c, [-0.5 0.5] * r);  ylim(c, [RE * 0.78 r * 1.06]);
title(c, sprintf('(c) Geometry:  sin\\eta = R_E cos\\epsilon / r,   \\lambda = 90%s - \\epsilon - \\eta', DEG), ...
      'FontWeight', 'normal');

% (d) LEO ve GEO kapsaması gerçek ölçekte
d = subplot(2, 2, 4); hold(d, 'on');
full = linspace(0, 2 * pi, 361);
[x, y] = pol(full, RE);    patch('Parent', d, 'XData', x, 'YData', y, 'FaceColor', earth, 'EdgeColor', [0.25 0.25 0.25]);
[x, y] = pol(full, r);     plot(d, x, y, '--', 'Color', [0.6 0.6 0.6]);
[x, y] = pol(full, RGEO);  plot(d, x, y, '--', 'Color', [0.6 0.6 0.6]);
lgeo = fp(RGEO, el_min);
sats = {0, r, lam0, serve; pi / 2, RGEO, lgeo, geoc};
for q = 1:2
    [th0, rr, lam, col] = sats{q, :};
    [ex, ey] = pol(linspace(th0 - lam, th0 + lam, 100), RE);
    [sx, sy] = pol(th0, rr);
    patch('Parent', d, 'XData', [sx ex], 'YData', [sy ey], 'FaceColor', col, 'FaceAlpha', 0.18, 'EdgeColor', 'none');
    [ex, ey] = pol(linspace(th0 - lam, th0 + lam, 100), RE * 1.01);
    plot(d, ex, ey, 'Color', col, 'LineWidth', 4);
    plot(d, sx, sy, 's', 'MarkerSize', 8, 'MarkerFaceColor', col, 'MarkerEdgeColor', 'k');
end
text(d, 0, r + 2500, sprintf('LEO: \\pm%.1f%s', lam0 / D, DEG), 'HorizontalAlignment', 'center', ...
     'Color', serve, 'FontWeight', 'bold', 'FontSize', 9);
text(d, RGEO + 1500, 0, sprintf('GEO: \\pm%.1f%s', lgeo / D, DEG), 'Color', geoc, 'FontWeight', 'bold', 'FontSize', 9);
capl = (1 - cos(lam0)) / 2;  capg = (1 - cos(lgeo)) / 2;
text(d, -RGEO * 1.05, -RGEO * 0.85, sprintf('Covered share of Earth surface:\n  one LEO sat: %.1f%%\n  one GEO sat: %.0f%%  (~%.0fx LEO)', ...
     100 * capl, 100 * capg, capg / capl), 'FontSize', 9);
set(d, 'DataAspectRatio', [1 1 1], 'XTick', [], 'YTick', [], 'Box', 'on');
xlim(d, [-1.1 1.25] * RGEO);  ylim(d, [-1.1 1.1] * RGEO);
title(d, sprintf('(d) LEO vs GEO coverage to scale (\\epsilon = %g%s)', el_min, DEG), 'FontWeight', 'normal');

% özet konsola
fprintf('LEO %g km, eps = %g deg: lambda = %.1f deg, radius = %.0f km, %.1f%% of Earth, N_min = %d (N = %d: %s)\n', ...
        h_leo, el_min, lam0 / D, lam0 * RE, 100 * capl, n0, n_sat, ternary(n_sat >= n0, 'continuous', 'GAPS'));
fprintf('GEO: lambda = %.1f deg, radius = %.0f km, %.0f%% of Earth\n', lgeo / D, lgeo * RE, 100 * capg);
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end

function s = deg_sym()
% Derece işareti: MATLAB karakterleri UTF-16, Octave ise UTF-8 bayt olarak tutar
if exist('OCTAVE_VERSION', 'builtin')
    s = char([194 176]);
else
    s = char(176);
end
end
