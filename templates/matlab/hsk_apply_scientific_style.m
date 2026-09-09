function palette = hsk_apply_scientific_style(fig, profile)
% HSK publication rendering style kernel.
% 只统一 palette / typography / ordinary Cartesian frame；不决定图型、数据、ylim、legend tile 或导出。
% 旧调用 hsk_apply_scientific_style(fig) 继续使用 competition_high_contrast。
arguments
    fig (1,1) matlab.ui.Figure = gcf
    profile (1,1) string = "competition_high_contrast"
end

profile = lower(strtrim(profile));
fontName = hsk_select_font();
palette = hsk_palette_profile(profile);
palette.fontName = fontName;
palette.profile = profile;

set(fig, "Color", "w");
axesList = findall(fig, "Type", "axes");
for ax = reshape(axesList, 1, [])
    % 普通二维数据图采用 open-axis publication frame；特殊 axes 可在调用后按证据结构覆盖。
    set(ax, "FontName", fontName, "FontSize", 16, ...
        "LineWidth", 1.15, "Box", "off", "Layer", "top", "TickDir", "out");
    grid(ax, "off");
    if isprop(ax, "XAxis") && isgraphics(ax.XAxis)
        set(ax.XAxis, "FontName", fontName);
    end
    if isprop(ax, "YAxis") && isgraphics(ax.YAxis)
        set(ax.YAxis, "FontName", fontName);
    end
    if isprop(ax, "ZAxis") && isgraphics(ax.ZAxis)
        set(ax.ZAxis, "FontName", fontName);
    end
    if isprop(ax, "XLabel") && isgraphics(ax.XLabel)
        set(ax.XLabel, "FontName", fontName, "FontSize", 18);
    end
    if isprop(ax, "YLabel") && isgraphics(ax.YLabel)
        set(ax.YLabel, "FontName", fontName, "FontSize", 18);
    end
end

textList = findall(fig, "Type", "text");
for txt = reshape(textList, 1, [])
    if isprop(txt, "FontName")
        set(txt, "FontName", fontName);
    end
end

legendList = findall(fig, "Type", "legend");
for lgd = reshape(legendList, 1, [])
    set(lgd, "FontName", fontName, "FontSize", 14, "Box", "off");
end

colorbarList = findall(fig, "Type", "colorbar");
for cb = reshape(colorbarList, 1, [])
    set(cb, "FontName", fontName, "FontSize", 14, "LineWidth", 1.0);
end

% 兼容旧脚本字段：无论 profile 如何选择，这些 release-era 字段仍保持原高对比值。
palette.brightBlue = [20, 120, 255] / 255;   % #1478FF
palette.vividRed = [240, 68, 68] / 255;       % #F04444
palette.brightGreen = [22, 179, 100] / 255;   % #16B364
palette.brightOrange = [247, 144, 9] / 255;   % #F79009
palette.brightPurple = [122, 90, 248] / 255;  % #7A5AF8
palette.darkGray = [37, 43, 55] / 255;        % #252B37
palette.lightGray = [233, 234, 235] / 255;    % #E9EAEB
palette.deepBlue = palette.brightBlue;
palette.midBlue = palette.brightBlue;
palette.teal = palette.brightGreen;
palette.brickRed = palette.vividRed;
palette.purple = palette.brightPurple;
palette.brownGray = palette.darkGray;
palette.darkRed = palette.vividRed;
palette.beige = palette.lightGray;
end

function palette = hsk_palette_profile(profile)
switch profile
    case "competition_high_contrast"
        % 高对比、中高饱和：少量核心对象、竞赛快速阅读。
        series = [
            20, 120, 255;   % #1478FF
            240, 68, 68;    % #F04444
            22, 179, 100;   % #16B364
            247, 144, 9;    % #F79009
            122, 90, 248    % #7A5AF8
        ] / 255;
        palette.primary = series(1,:);
        palette.comparison = series(2,:);
        palette.positive = series(3,:);
        palette.accent = series(4,:);
        palette.secondary = series(5,:);
        palette.focus = series(4,:);
        palette.context = [154, 164, 178] / 255;
        palette.neutral = [207, 206, 206] / 255;
    case "journal_balanced"
        % 成熟期刊式多对象 palette：navy / muted green-red / teal-violet。
        series = [
            15, 77, 146;    % #0F4D92 navy
            55, 117, 186;   % #3775BA blue
            139, 207, 139;  % #8BCF8B green
            182, 67, 66;    % #B64342 muted red
            66, 148, 158;   % #42949E teal
            154, 77, 142;   % #9A4D8E violet
            170, 220, 169;  % #AADCA9 soft green
            233, 166, 161   % #E9A6A1 soft red
        ] / 255;
        palette.primary = series(1,:);
        palette.comparison = series(4,:);
        palette.positive = series(3,:);
        palette.accent = series(5,:);
        palette.secondary = series(6,:);
        palette.focus = [255, 215, 0] / 255;   % #FFD700
        palette.context = [185, 185, 185] / 255;
        palette.neutral = [207, 206, 206] / 255; % #CFCECE
    case "monochrome_print"
        series = [
            25, 25, 25;
            80, 80, 80;
            125, 125, 125;
            165, 165, 165;
            205, 205, 205
        ] / 255;
        palette.primary = series(1,:);
        palette.comparison = series(2,:);
        palette.positive = series(3,:);
        palette.accent = series(2,:);
        palette.secondary = series(4,:);
        palette.focus = series(1,:);
        palette.context = series(4,:);
        palette.neutral = series(5,:);
    otherwise
        error("未知 publication palette profile: %s", profile);
end
palette.series = series;
palette.dark = [37, 43, 55] / 255;
palette.light = [233, 234, 235] / 255;
palette.background = [1, 1, 1];
end

function fontName = hsk_select_font()
preferred = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", ...
    "Arial Unicode MS", "Helvetica", "Arial"];
available = string(listfonts);
fontName = "Helvetica";
for candidate = preferred
    if any(strcmpi(available, candidate))
        fontName = candidate;
        return;
    end
end
end
