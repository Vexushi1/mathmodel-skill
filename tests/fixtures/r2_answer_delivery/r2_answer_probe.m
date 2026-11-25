function filename = r2_answer_probe(projectRoot, scenario)
payload = jsondecode(fileread(fullfile(projectRoot,"input.json")));
times = reshape(payload.times, 1, []);
values = payload.cases.(char(scenario));
stations = string(payload.stations);
peaks = {'记录键','站点','峰值','时刻','单位','时间单位'};
events = {'站点','状态','时刻','原因'};
for station = 1:numel(stations)
    peak = max(values(station,:));
    indices = find(values(station,:) == peak);
    for index = indices
        key = scenario + "-" + stations(station) + "-" + string(times(index));
        peaks(end+1,:) = {key, stations(station), peak, times(index), "1", "s"}; %#ok<AGROW>
    end
    triggered = find(values(station,:) >= payload.threshold, 1);
    if isempty(triggered)
        events(end+1,:) = {stations(station), "未触发", "", "全部采样值低于阈值"}; %#ok<AGROW>
    else
        events(end+1,:) = {stations(station), "已触发", times(triggered), "达到阈值"}; %#ok<AGROW>
    end
end
sheets = {
    '运行配置', {'项目','值';'execution_owner','user';'execution_profile','full_fidelity';'stage','primary'};
    '核心指标', {'指标','数值';'全网峰值',max(sum(values,1))};
    '数据审计', {'等级','检查项','信息','处理方式';'Info','事件时刻','未触发事件的时刻缺失','保留空值、状态与原因'};
    '主结果质量门', {'检查项','是否通过','证据';'逐站峰值',true,'每站保留全部并列峰时'};
    '站点峰值', peaks;
    '执行停止证据', {'迭代或样本数','指标','数值','单位';numel(times),'末采样时刻',times(end),'s'};
    '事件状态', events;
};
folder = fullfile(projectRoot,scenario,"问题一求解");
if ~isfolder(folder), mkdir(folder); end
filename = fullfile(folder,"问题一求解结果.xlsx");
write_workbook(filename,sheets);
end

