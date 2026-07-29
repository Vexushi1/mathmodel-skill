function hsk_export_figure(fig, outputBase, formats)
% 人工调整完成后显式调用；默认不由绘图脚本自动触发。
arguments
    fig (1,1) matlab.ui.Figure
    outputBase (1,1) string
    formats (1,:) string = ["pdf", "png"]
end
outDir = fileparts(outputBase);
if strlength(outDir) > 0 && ~isfolder(outDir)
    mkdir(outDir);
end
for fmt = formats
    switch lower(fmt)
        case "pdf"
            exportgraphics(fig, outputBase + ".pdf", "ContentType", "vector");
        case "png"
            exportgraphics(fig, outputBase + ".png", "Resolution", 600);
        case "svg"
            exportgraphics(fig, outputBase + ".svg", "ContentType", "vector");
        otherwise
            error("不支持的导出格式: %s", fmt);
    end
end
end
