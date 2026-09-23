function palette = hsk_apply_scientific_style(fig, profile, style)
%HSK_APPLY_SCIENTIFIC_STYLE Base typography/frame without implicit colors.
% 创建绘图对象、标签、legend/colorbar 后调用一次，再做当前图的局部覆盖。
% 不设置 Color、ColorOrder 或 colormap；白底和数据颜色由实例脚本显式选择。
% 空 profile 只做基础排版并返回空 palette；需要旧颜色角色时必须显式指定 profile。
arguments
    fig (1,1) matlab.ui.Figure = gcf
    profile (1,1) string = ""
    style (1,1) struct = struct()
end

assert(isgraphics(fig, "figure"), "fig 必须为有效 figure");
spec = hsk_publication_profile(profile);
defaults = struct("fontName", "", ...
    "axesFontSize", spec.typography.axes_font_size, ...
    "labelFontSize", spec.typography.label_font_size, ...
    "legendFontSize", spec.typography.legend_font_size, ...
    "colorbarFontSize", spec.typography.colorbar_font_size, ...
    "axesLineWidth", spec.frame.axes_line_width, ...
    "colorbarLineWidth", spec.frame.colorbar_line_width);
% frame.background 仅为白底参考；颜色仍由实例脚本显式设置。
fontName = apply_base_style(fig, style, defaults, spec.frame);
palette = spec.palette;
if ~isempty(fieldnames(palette))
    palette.fontName = fontName;
    palette.profile = spec.name;
end
end

function fontName = apply_base_style(fig, overrides, defaults, frame)
% 与独立入口 fallback 保持相同实现；先完整验证，再修改任何图形属性。
style = checked_style(overrides, defaults);
assert(isstring(frame.box) && isscalar(frame.box) && any(frame.box == ["on", "off"]), ...
    "基础 frame.box 必须为 on 或 off");
assert(isstring(frame.tick_dir) && isscalar(frame.tick_dir) && ...
    any(frame.tick_dir == ["in", "out", "both"]), "基础 frame.tick_dir 无效");
assert(isstring(frame.grid) && isscalar(frame.grid) && any(frame.grid == ["on", "off"]), ...
    "基础 frame.grid 必须为 on 或 off");
fontName = style.fontName;
if strlength(fontName) == 0
    fontName = select_style_font();
end

% findobj 不穿透隐藏图表内部；只处理公开的普通 axes。
for ax = reshape(findobj(fig, "Type", "axes"), 1, [])
    set(ax, "FontName", fontName, "FontUnits", "points", ...
        "FontSize", style.axesFontSize, "LineWidth", style.axesLineWidth);
    if isequal(ax.View, [0, 90])
        set(ax, "Box", frame.box, "Layer", "top", "TickDir", frame.tick_dir);
        grid(ax, frame.grid);
    end
    % yyaxis 的 YAxis 可有两个 ruler；逐个访问 Label，不切换活动侧。
    for axisName = ["XAxis", "YAxis", "ZAxis"]
        for ruler = reshape(ax.(axisName), 1, [])
            if isprop(ruler, "Label") && isgraphics(ruler.Label, "text")
                set(ruler.Label, "FontName", fontName, "FontUnits", "points", ...
                    "FontSize", style.labelFontSize);
            end
        end
    end
end

% 极坐标不套用 Cartesian 的 open-axis/grid 规则。
for ax = reshape(findobj(fig, "Type", "polaraxes"), 1, [])
    set(ax, "FontName", fontName, "FontUnits", "points", ...
        "FontSize", style.axesFontSize, "LineWidth", style.axesLineWidth);
end
% HeatmapChart 只有公共统一字号，不访问隐藏 axes 或把文字标签当 Text。
for chart = reshape(findobj(fig), 1, [])
    if isa(chart, "matlab.graphics.chart.HeatmapChart")
        set(chart, "FontName", fontName, "FontSize", style.axesFontSize);
    end
end
for txt = reshape(findobj(fig, "Type", "text"), 1, [])
    set(txt, "FontName", fontName);
end

% axes 字号可能影响关联对象，因此 legend/colorbar 最后设置。
for lgd = reshape(findobj(fig, "Type", "legend"), 1, [])
    set(lgd, "FontName", fontName, "FontUnits", "points", ...
        "FontSize", style.legendFontSize, "Box", "off");
end
for cb = reshape(findobj(fig, "Type", "colorbar"), 1, [])
    set(cb, "FontName", fontName, ...
        "FontSize", style.colorbarFontSize, "LineWidth", style.colorbarLineWidth);
    set(cb.Label, "FontName", fontName, "FontUnits", "points", ...
        "FontSize", style.colorbarFontSize);
end
end

function style = checked_style(overrides, defaults)
assert(isstruct(overrides) && isscalar(overrides), "style 必须为标量 struct");
style = defaults;
names = fieldnames(overrides);
unknown = setdiff(names, fieldnames(style));
assert(isempty(unknown), "未知 style 字段: %s", strjoin(string(unknown), ", "));
for i = 1:numel(names)
    style.(names{i}) = overrides.(names{i});
end
names = fieldnames(style);
for i = 1:numel(names)
    name = names{i};
    value = style.(name);
    if strcmp(name, "fontName")
        isText = (ischar(value) && (isrow(value) || isequal(size(value), [0, 0]))) || ...
            (isstring(value) && isscalar(value) && ~ismissing(value));
        assert(isText, "style.fontName 必须为非缺测标量文本；空文本表示本机字体候选");
        style.fontName = strtrim(string(value));
    else
        assert(isnumeric(value) && isscalar(value) && isreal(value) && ...
            isfinite(value) && value > 0, "style.%s 必须为有限正实标量", name);
        style.(name) = double(value);
    end
end
end

function fontName = select_style_font()
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
