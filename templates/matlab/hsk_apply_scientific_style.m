function palette = hsk_apply_scientific_style(fig)
% 应用统一科研基础风格；不导出、不关闭图窗，并提供跨平台字体回退。
% 返回的 palette 是默认规则色板，不是固定限制；问题脚本可按变量语义和图型调整。
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
        set(ax.Title, "FontName", fontName);
    end
    if isprop(ax, "XAxis") && isgraphics(ax.XAxis)
        set(ax.XAxis, "FontName", fontName);
    end
    if isprop(ax, "YAxis") && isgraphics(ax.YAxis)
        set(ax.YAxis, "FontName", fontName);
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

textList = findall(fig, "Type", "text");
for txt = reshape(textList, 1, [])
    if isprop(txt, "FontName")
        set(txt, "FontName", fontName);
    end
end

palette.deepBlue = [23, 59, 94] / 255;
palette.midBlue = [55, 92, 135] / 255;
palette.teal = [30, 117, 107] / 255;
palette.darkRed = [154, 56, 56] / 255;
palette.purple = [93, 75, 134] / 255;
palette.beige = [169, 143, 112] / 255;
palette.darkGray = [32, 38, 46] / 255;
palette.lightGray = [217, 218, 215] / 255;
palette.fontName = fontName;
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
