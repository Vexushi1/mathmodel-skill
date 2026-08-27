function palette = hsk_apply_scientific_style(fig)
% 应用统一科研基础风格；正式论文图不设置整体title/sgtitle，不导出、不关闭图窗，并提供字体回退。
% 返回 palette 只是低饱和实体科研配色起点，不是固定模板；问题脚本仍应按变量语义和 Figure Contract 调整。
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
    if isprop(ax, "XAxis") && isgraphics(ax.XAxis)
        set(ax.XAxis, "FontName", fontName);
    end
    if isprop(ax, "YAxis") && isgraphics(ax.YAxis)
        set(ax.YAxis, "FontName", fontName);
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
    set(lgd, "FontName", fontName, "FontSize", 16, "Box", "off");
end

colorbarList = findall(fig, "Type", "colorbar");
for cb = reshape(colorbarList, 1, [])
    set(cb, "FontName", fontName, "FontSize", 16, "LineWidth", 1.2);
end

% 主比较色：实体、低饱和、可区分；辅助对象继续使用灰色或透明度降权。
palette.deepBlue = [23, 59, 94] / 255;       % #173B5E
palette.midBlue = [55, 92, 135] / 255;       % #375C87
palette.teal = [30, 117, 107] / 255;         % #1E756B
palette.brickRed = [154, 56, 56] / 255;      % #9A3838
palette.purple = [93, 75, 134] / 255;        % #5D4B86
palette.brownGray = [169, 143, 112] / 255;   % #A98F70
palette.darkGray = [32, 38, 46] / 255;       % #20262E
palette.lightGray = [217, 218, 215] / 255;   % #D9DAD7
palette.fontName = fontName;

% 兼容旧脚本字段名；只保留字段可读兼容，不恢复旧高饱和色板。
palette.brightBlue = palette.deepBlue;
palette.vividRed = palette.brickRed;
palette.brightGreen = palette.teal;
palette.brightOrange = palette.brownGray;
palette.brightPurple = palette.purple;
palette.darkRed = palette.brickRed;
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
