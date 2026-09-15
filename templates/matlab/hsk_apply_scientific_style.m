function palette = hsk_apply_scientific_style(fig, profile)
% HSK publication rendering style kernel.
% 只把已选择的 publication profile 应用于 figure；不决定图型、数据、ylim、legend tile 或导出。
% profile 数据由 hsk_publication_profile.m 唯一提供；旧调用仍默认 competition_high_contrast。
arguments
    fig (1,1) matlab.ui.Figure = gcf
    profile (1,1) string = "competition_high_contrast"
end

profile = lower(strtrim(profile));
spec = hsk_publication_profile(profile);
fontName = hsk_select_font();
palette = spec.palette;
palette.fontName = fontName;
palette.profile = spec.name;

set(fig, "Color", spec.frame.background);
axesList = findall(fig, "Type", "axes");
for ax = reshape(axesList, 1, [])
    % 普通二维数据图采用 open-axis publication frame；特殊 axes 可在调用后按证据结构覆盖。
    set(ax, "FontName", fontName, "FontSize", spec.typography.axes_font_size, ...
        "LineWidth", spec.frame.axes_line_width, "Box", spec.frame.box, ...
        "Layer", "top", "TickDir", spec.frame.tick_dir);
    grid(ax, spec.frame.grid);
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
        set(ax.XLabel, "FontName", fontName, "FontSize", spec.typography.label_font_size);
    end
    if isprop(ax, "YLabel") && isgraphics(ax.YLabel)
        set(ax.YLabel, "FontName", fontName, "FontSize", spec.typography.label_font_size);
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
    set(lgd, "FontName", fontName, "FontSize", spec.typography.legend_font_size, "Box", "off");
end

colorbarList = findall(fig, "Type", "colorbar");
for cb = reshape(colorbarList, 1, [])
    set(cb, "FontName", fontName, "FontSize", spec.typography.colorbar_font_size, ...
        "LineWidth", spec.frame.colorbar_line_width);
end
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
