"""
Test for unwanted reference cycles

"""
import warnings
import weakref

import numpy as np

import pyqtgraph as pg

app = pg.mkQApp()

def assert_alldead(refs):
    for ref in refs:
        assert ref() is None

def qObjectTree(root):
    """Return root and its entire tree of qobject children"""
    childs = [root]
    for ch in pg.QtCore.QObject.children(root):
        childs += qObjectTree(ch)
    return childs

def mkrefs(*objs):
    """Return a list of weakrefs to each object in *objs.
    QObject instances are expanded to include all child objects.
    """
    allObjs = {}
    for obj in objs:
        obj = qObjectTree(obj) if isinstance(obj, pg.QtCore.QObject) else [obj]
        for o in obj:
            allObjs[id(o)] = o
    return [weakref.ref(obj) for obj in allObjs.values()]


def test_PlotWidget():
    def mkobjs(*args, **kwds):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w = pg.PlotWidget(*args, **kwds)
        data = np.array([1,5,2,4,3])
        c = w.plot(data, name='stuff')
        w.addLegend()
        
        # test that connections do not keep objects alive
        w.plotItem.vb.sigRangeChanged.connect(mkrefs)
        app.focusChanged.connect(w.plotItem.vb.invertY)
        
        # return weakrefs to a bunch of objects that should die when the scope exits.
        return mkrefs(w, c, data, w.plotItem, w.plotItem.vb, w.plotItem.getMenu(), w.plotItem.getAxis('left'))
    
    for _ in range(5):
        assert_alldead(mkobjs())


def test_ImageView():
    def mkobjs():
        iv = pg.ImageView()
        data = np.zeros((10,10,5))
        iv.setImage(data)
        
        return mkrefs(iv, iv.imageItem, iv.view, iv.ui.histogram, data)

    for _ in range(5):
        assert_alldead(mkobjs())
