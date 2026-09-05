function fig = draw_mechanism_structure(nodes, edges, positions)
% 题目专属结构图骨架。调用者必须提供真实对象、关系和坐标；无通用默认节点。
arguments
    nodes (1,:) string
    edges (:,2) double
    positions (:,2) double
end
assert(numel(nodes) == size(positions,1), "节点数与坐标行数不一致");
assert(all(edges(:) >= 1 & edges(:) <= numel(nodes)), "边索引超出节点范围");
fig = figure("Color", "w", "Position", [100, 100, 900, 620]);
ax = axes(fig); hold(ax, "on"); axis(ax, "equal"); axis(ax, "off");
for k = 1:size(edges,1)
    p1 = positions(edges(k,1),:); p2 = positions(edges(k,2),:);
    quiver(ax, p1(1), p1(2), p2(1)-p1(1), p2(2)-p1(2), 0, ...
        "Color", [0.15,0.15,0.15], "LineWidth", 1.6, "MaxHeadSize", 0.12);
end
scatter(ax, positions(:,1), positions(:,2), 80, "filled", ...
    "MarkerFaceColor", [0.95,0.95,0.95], "MarkerEdgeColor", [0.1,0.1,0.1]);
for i = 1:numel(nodes)
    text(ax, positions(i,1), positions(i,2), nodes(i), "HorizontalAlignment", "center", ...
        "VerticalAlignment", "bottom", "FontSize", 16);
end
hsk_apply_scientific_style(fig);
end
