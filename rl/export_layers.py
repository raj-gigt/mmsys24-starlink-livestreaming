"""Serialize dense actor layers without importing historical reference exporters."""
def layer(state,name):
    return {'shape':list(state[name+'.weight'].shape),
            'w':state[name+'.weight'].flatten().tolist(),'b':state[name+'.bias'].tolist()}
