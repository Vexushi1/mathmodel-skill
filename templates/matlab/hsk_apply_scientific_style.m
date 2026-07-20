function palette = hsk_apply_scientific_style(fig)
% 应用统一科研风格；不导出、不关闭图窗。
arguments
    fig (1,1) matlab.ui.Figure = gcf
end
set(fig, "Color", "w");
axesList = findall(fig, "Type", "axes");
for ax = reshape(axesList, 1, [])
    set(ax, "FontName", "Microsoft YaHei", "FontSize", 18, ...
        "LineWidth", 1.4, "Box", "on", "Layer", "top");
    grid(ax, "off");
end
palette.deepBlue = [23, 59, 94] / 255;
palette.midBlue = [55, 92, 135] / 255;
palette.teal = [30, 117, 107] / 255;
palette.darkRed = [154, 56, 56] / 255;
palette.purple = [93, 75, 134] / 255;
palette.beige = [169, 143, 112] / 255;
palette.darkGray = [32, 38, 46] / 255;
palette.lightGray = [217, 218, 215] / 255;
end
