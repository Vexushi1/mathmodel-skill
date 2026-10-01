function [coefficients, prediction, normalResidual] = hsk_comparison_fit(t, y, degree, method, evaluationT)
% Explicit QR/SVD polynomial micro-example; replace the model for real tasks.
t = double(t(:));
y = double(y(:));
validateattributes(t, {'numeric'}, {'finite','real','column'});
validateattributes(y, {'numeric'}, {'finite','real','column','numel',numel(t)});
design = t .^ (0:degree);
if method == "QR"
    [Q,R] = qr(design,0);
    assert(min(abs(diag(R))) > eps * norm(R), 'HSK:Rank', 'QR design is rank deficient.');
    coefficients = R \ (Q.' * y);
elseif method == "SVD"
    [U,S,V] = svd(design,0);
    singular = diag(S);
    assert(singular(end) > eps * max(size(design)) * singular(1), ...
        'HSK:Rank', 'SVD design is rank deficient.');
    coefficients = V * ((U.' * y) ./ singular);
else
    error('HSK:Method', 'This example supports explicit QR or SVD only.');
end
prediction = double(evaluationT(:)) .^ (0:degree) * coefficients;
normalResidual = max(abs(design.' * (design * coefficients - y)));
assert(all(isfinite(coefficients)) && all(isfinite(prediction)), 'HSK:Finite', 'Nonfinite polynomial result.');
end
