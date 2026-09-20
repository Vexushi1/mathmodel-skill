function spec = hsk_publication_profile(profile)
%HSK_PUBLICATION_PROFILE Explicit palette candidates and base typography/frame.
% 省略 profile 或传入空字符串时 palette 为空；不隐式选择任何颜色。
% 返回 palette / typography / ordinary Cartesian frame 的纯配置；
% 不创建/修改 figure，不读取工作簿，不选择图型、legend、layout、ylim 或导出策略。
arguments
    profile (1,1) string = ""
end

profile = lower(strtrim(profile));
assert(~ismissing(profile), "profile 必须为非缺测标量文本；空字符串只请求基础排版");
if strlength(profile) == 0
    spec = base_spec(profile, struct());
    return;
end

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

% Release-era aliases remain byte-semantically compatible with v9.1 callers.
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

spec = base_spec(profile, palette);
end

function spec = base_spec(profile, palette)
spec.name = profile;
spec.palette = palette;
spec.typography.axes_font_size = 16;
spec.typography.label_font_size = 18;
spec.typography.legend_font_size = 14;
spec.typography.colorbar_font_size = 14;
spec.frame.axes_line_width = 1.15;
spec.frame.colorbar_line_width = 1.0;
spec.frame.box = "off";
spec.frame.tick_dir = "out";
spec.frame.grid = "off";
spec.frame.background = [1, 1, 1];
end
