from score_sensitivity import score
m={'quality_utility':2,'stall_s':1,'startup_s':1,'variation':.5,'latency_area':2,'duration_s':10}
assert abs(score(m)-(-.335))<1e-12
assert abs(score(m,stall=2)-(-.135))<1e-12
assert abs(score(m,variation=.6)-(-.35))<1e-12
print('PASS: hand-calculated base and coefficient sensitivity')
