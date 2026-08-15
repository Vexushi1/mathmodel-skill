function palette = hsk_apply_scientific_style(fig)
% 应用统一科研基础风格；保留简洁标题，不导出、不关闭图窗，并提供字体回退。
% 返回 palette 只是高对比起点，不是固定模板；问题脚本仍应按变量语义和 Figure Contract 调整。
arguments
    fig (1,1) matlab.ui.Figure = gcf
end

fontName = hsk_select_font();
set(fig, "Color", "w");

axesList = findall(fig, "Type", "axes");
for ax = reshape(axesList, 1, [])
    set(ax, "FontName", fontName, "FontSize", 18, ...
        "LineWidth", 1.4, "Box", "on", "Layer", "top");
    grid(ax, "off");
    if isprop(ax, "Title") && isgraphics(ax.Title)
        set(ax.Title, "FontName", fontName, "FontSize", 18, ...
            "FontWeight", "normal");
    end
    if isprop(ax, "XAxis") && isgraphics(ax.XAxis)
        set(ax.XAxis, "FontName", fontName);
    end
    if isprop(ax, "YAxis") && isgraphics(ax.YAxis)
        set(ax.YAxis, "FontName", fontName);
    end
end

% tiledlayout 的 sgtitle 通常表现为 annotation/text；统一字体但不删除标题。
textList = findall(fig, "Type", "text");
for txt = reshape(textList, 1, [])
    if isprop(txt, "FontName")
        set(txt, "FontName", fontName);
    end
    if isprop(txt, "FontWeight") && contains(string(txt.Tag), "Title", "IgnoreCase", true)
        set(txt, "FontWeight", "normal");
    end
end

legendList = findall(fig, "Type", "legend");
for lgd = reshape(legendList, 1, [])
    set(lgd, "FontName", fontName, "FontSize", 16, "Box", "off");
end

colorbarList = findall(fig, "Type", "colorbar");
for cb = reshape(colorbarList, 1, [])
    set(cb, "FontName", fontName, "FontSize", 16, "LineWidth", 1.2);
end

% 主比较色：中高饱和、高对比，优先让评委第一眼识别差异。
palette.brightBlue = [20, 120, 255] / 255;   % #1478FF
palette.vividRed = [240, 68, 68] / 255;       % #F04444
palette.brightGreen = [22, 179, 100] / 255;   % #16B364
palette.brightOrange = [247, 144, 9] / 255;   % #F79009
palette.brightPurple = [122, 90, 248] / 255;  % #7A5AF8
palette.darkGray = [37, 43, 55] / 255;        % #252B37
palette.lightGray = [233, 234, 235] / 255;    % #E9EAEB
palette.fontName = fontName;

% 兼容旧脚本字段名，但映射到当前高对比色板，避免旧模板继续传播低饱和先验。
palette.deepBlue = palette.brightBlue;
palette.midBlue = palette.brightBlue;
palette.teal = palette.brightGreen;
palette.darkRed = palette.vividRed;
palette.purple = palette.brightPurple;
palette.beige = palette.lightGray;
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
