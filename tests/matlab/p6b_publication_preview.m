function p6b_publication_preview(outputDir)
%P6B_PUBLICATION_PREVIEW Render and machine-check representative publication previews.
% This harness validates implementation only. Synthetic data are not modeling evidence.
arguments
    outputDir (1,1) string
end

repoRoot = string(fileparts(fileparts(fileparts(mfilename("fullpath")))));
addpath(fullfile(repoRoot, "templates", "matlab"));

if isfolder(outputDir)
    rmdir(outputDir, "s");
end
mkdir(outputDir);

profiles = ["competition_high_contrast", "journal_balanced", "monochrome_print"];
reports = repmat(struct("profile", "", "font", "", "png", "", "pdf", "", ...
    "png_bytes", 0, "pdf_bytes", 0, "image_height", 0, "image_width", 0), 1, numel(profiles));

for i = 1:numel(profiles)
    profile = profiles(i);
    spec = hsk_publication_profile(profile);
    fig = build_preview(profile, spec);
    cleaner = onCleanup(@() close_if_valid(fig)); %#ok<NASGU>
    palette = hsk_apply_scientific_style(fig, profile);

    verify_runtime_style(fig, spec, palette, profile);

    pngPath = fullfile(outputDir, profile + ".png");
    pdfPath = fullfile(outputDir, profile + ".pdf");
    exportgraphics(fig, pngPath, "Resolution", 180);
    exportgraphics(fig, pdfPath, "ContentType", "vector");

    pngInfo = dir(pngPath);
    pdfInfo = dir(pdfPath);
    assert(~isempty(pngInfo) && pngInfo.bytes > 10000, "PNG preview is missing or unexpectedly small: %s", pngPath);
    assert(~isempty(pdfInfo) && pdfInfo.bytes > 3000, "PDF preview is missing or unexpectedly small: %s", pdfPath);

    imageData = imread(pngPath);
    assert(size(imageData, 1) >= 600 && size(imageData, 2) >= 900, ...
        "Preview canvas is unexpectedly small for %s", profile);
    rgb = double(imageData(:, :, 1:min(3, size(imageData, 3))));
    assert(std(rgb(:)) > 3.0, "Preview appears blank or nearly uniform for %s", profile);

    reports(i).profile = char(profile);
    reports(i).font = char(palette.fontName);
    reports(i).png = char(profile + ".png");
    reports(i).pdf = char(profile + ".pdf");
    reports(i).png_bytes = pngInfo.bytes;
    reports(i).pdf_bytes = pdfInfo.bytes;
    reports(i).image_height = size(imageData, 1);
    reports(i).image_width = size(imageData, 2);

    close(fig);
    clear cleaner;
end

report.matlab_version = version;
report.matlab_release = version("-release");
report.profiles = reports;
report.machine_checks = ["profile_api", "style_application", "text", "legend", ...
    "canvas", "png_pdf_export", "nonblank_raster", "monochrome_print_safe", "output_boundary"];
reportPath = fullfile(outputDir, "preview_report.json");
fid = fopen(reportPath, "w");
assert(fid ~= -1, "Cannot create preview report: %s", reportPath);
fprintf(fid, "%s\n", jsonencode(report, PrettyPrint=true));
fclose(fid);

expected = sort([profiles + ".png", profiles + ".pdf", "preview_report.json"]);
listing = dir(outputDir);
actual = string({listing(~[listing.isdir]).name});
assert(isequal(sort(actual), expected), ...
    "Preview output boundary violated. Expected: %s; actual: %s", ...
    strjoin(expected, ", "), strjoin(sort(actual), ", "));
end

function fig = build_preview(profile, spec)
fig = figure("Visible", "off", "Color", "w", "Units", "pixels", "Position", [100, 100, 1200, 760]);
tl = tiledlayout(fig, 1, 2, "TileSpacing", "compact", "Padding", "compact");

x = linspace(0, 10, 121);
ax1 = nexttile(tl, 1);
hold(ax1, "on");
styles = ["-", "--", "-."];
markers = ["none", "o", "s"];
for k = 1:3
    y = 0.45 * k + sin(x * (0.45 + 0.08 * k)) .* exp(-0.04 * k * x);
    plot(ax1, x, y, "LineWidth", 2.0, "LineStyle", styles(k), ...
        "Marker", markers(k), "MarkerIndices", 1:20:numel(x), ...
        "Color", spec.palette.series(k, :), "DisplayName", "Series " + k);
end
xlabel(ax1, "Normalized input");
ylabel(ax1, "Response");
legend(ax1, "Location", "best");

ax2 = nexttile(tl, 2);
if profile == "journal_balanced"
    matrix = sin((1:18)' * 0.23) * cos((1:24) * 0.17) + 0.08 * ((1:18)' - 9);
    imagesc(ax2, matrix);
    axis(ax2, "tight");
    colormap(ax2, parula(128));
    cb = colorbar(ax2);
    cb.Label.String = "Relative intensity";
    xlabel(ax2, "Parameter index");
    ylabel(ax2, "Scenario index");
    hold(ax2, "on");
    plot(ax2, [4, 20], [4, 15], "-", "Color", spec.palette.focus, ...
        "LineWidth", 2.0, "DisplayName", "Focus path");
    legend(ax2, "Location", "southoutside");
else
    categories = categorical(["A", "B", "C", "D", "E"]);
    values = [0.72, 0.91, 0.81, 0.64, 0.86];
    b = bar(ax2, categories, values, 0.62, "FaceColor", "flat", "DisplayName", "Score");
    b.CData = spec.palette.series(mod((0:4), size(spec.palette.series, 1)) + 1, :);
    ylim(ax2, [0, 1.05]);
    xlabel(ax2, "Candidate");
    ylabel(ax2, "Normalized score");
    hold(ax2, "on");
    yline(ax2, 0.80, "--", "Reference", "LineWidth", 1.4, ...
        "Color", spec.palette.context, "LabelHorizontalAlignment", "left");
    legend(ax2, "Location", "southoutside");
end
end

function verify_runtime_style(fig, spec, palette, profile)
assert(isequal(round(fig.Position(3:4)), [1200, 760]), "Figure canvas changed unexpectedly.");
assert(max(abs(fig.Color - spec.frame.background)) < 1e-12, "Figure background does not match profile spec.");
assert(string(palette.profile) == profile, "Applied profile name does not match requested profile.");
assert(strlength(string(palette.fontName)) > 0, "Runtime font selection returned an empty font.");

axesList = findall(fig, "Type", "axes");
assert(numel(axesList) == 2, "Representative preview must contain exactly two data axes.");
for ax = reshape(axesList, 1, [])
    assert(abs(ax.FontSize - spec.typography.axes_font_size) < 1e-12, "Axes font size mismatch.");
    assert(abs(ax.LineWidth - spec.frame.axes_line_width) < 1e-12, "Axes line width mismatch.");
    assert(strcmpi(ax.Box, spec.frame.box), "Axes box mode mismatch.");
    assert(strcmpi(ax.TickDir, spec.frame.tick_dir), "Axes tick direction mismatch.");
    assert(strlength(string(ax.FontName)) > 0, "Axes font is empty.");
    assert(strlength(string(ax.XLabel.String)) > 0, "X label is missing.");
    assert(strlength(string(ax.YLabel.String)) > 0, "Y label is missing.");
    assert(strlength(string(ax.Title.String)) == 0, "Formal preview must not contain an in-figure title.");
end

legendList = findall(fig, "Type", "legend");
assert(~isempty(legendList), "Representative preview must include a legend.");
for lgd = reshape(legendList, 1, [])
    assert(abs(lgd.FontSize - spec.typography.legend_font_size) < 1e-12, "Legend font size mismatch.");
    assert(strcmpi(lgd.Box, "off"), "Legend box must be off.");
    assert(strlength(string(lgd.FontName)) > 0, "Legend font is empty.");
end

if profile == "journal_balanced"
    colorbarList = findall(fig, "Type", "colorbar");
    assert(numel(colorbarList) == 1, "Journal preview must include one colorbar.");
    cb = colorbarList(1);
    assert(abs(cb.FontSize - spec.typography.colorbar_font_size) < 1e-12, "Colorbar font size mismatch.");
    assert(abs(cb.LineWidth - spec.frame.colorbar_line_width) < 1e-12, "Colorbar line width mismatch.");
end

if profile == "monochrome_print"
    series = spec.palette.series;
    assert(max(abs(series(:, 1) - series(:, 2))) < 1e-12 && ...
           max(abs(series(:, 2) - series(:, 3))) < 1e-12, ...
           "monochrome_print palette is not grayscale/print-safe.");
end
end

function close_if_valid(fig)
if isgraphics(fig)
    close(fig);
end
end
