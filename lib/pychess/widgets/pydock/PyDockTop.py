from __future__ import absolute_import
from __future__ import print_function

import os
from xml.dom import minidom

from gi.repository import Gtk
from gi.repository import GObject

from pychess.System.prefix import addDataPrefix

from .PyDockLeaf import PyDockLeaf
from .PyDockComposite import PyDockComposite
from .ArrowButton import ArrowButton
from .HighlightArea import HighlightArea
from .__init__ import TopDock, DockLeaf, DockComponent, DockComposite
from .__init__ import NORTH, EAST, SOUTH, WEST, CENTER

class PyDockTop (TopDock):
    def __init__ (self, id):
        TopDock.__init__(self, id)
        self.set_no_show_all(True)
        
        self.highlightArea = HighlightArea(self)
        
        self.buttons = (ArrowButton(self, addDataPrefix("glade/dock_top.svg"), NORTH),
                        ArrowButton(self, addDataPrefix("glade/dock_right.svg"), EAST),
                        ArrowButton(self, addDataPrefix("glade/dock_bottom.svg"), SOUTH),
                        ArrowButton(self, addDataPrefix("glade/dock_left.svg"), WEST))
        
        for button in self.buttons:
            button.connect("dropped", self.__onDrop)
            button.connect("hovered", self.__onHover)
            button.connect("left", self.__onLeave)
    
    def _del (self):
        TopDock._del(self)

    def __repr__ (self):
        return "top (%s) % self.id"
    
    #===========================================================================
    #    Component stuff
    #===========================================================================
    
    def addComponent (self, widget):
        self.add(widget)
        widget.show()
    
    def changeComponent (self, old, new):
        self.removeComponent(old)
        self.addComponent(new)
    
    def removeComponent (self, widget):
        self.remove(widget)
    
    def getComponents (self):
        if isinstance(self.get_child(), DockComponent):
            return [self.get_child()]
        return []
    
    def dock (self, widget, position, title, id):
        if not self.getComponents():
            leaf = PyDockLeaf(widget, title, id)
            self.addComponent(leaf)
            return leaf
        else:
            return self.get_child().dock(widget, position, title, id)
    
    def clear (self):
        self.remove(self.get_child())
    
    #===========================================================================
    #    Signals
    #===========================================================================
    
    def showArrows (self):
        for button in self.buttons:
            button._calcSize()
            button.show()
    
    def hideArrows (self):
        for button in self.buttons:
            button.hide()
        self.highlightArea.hide()
    
    def __onDrop (self, arrowButton, sender):
        self.highlightArea.hide()
        child = sender.get_nth_page(sender.get_current_page())
        title, id = sender.get_parent().undock(child)
        self.dock(child, arrowButton.myposition, title, id)
    
    def __onHover (self, arrowButton, widget):
        self.highlightArea.showAt(arrowButton.myposition)
        arrowButton.get_window().raise_()
    
    def __onLeave (self, arrowButton):
        self.highlightArea.hide()
    
    #===========================================================================
    #    XML
    #===========================================================================
    
    def saveToXML (self, xmlpath):
        dockElem = None
        
        if os.path.isfile(xmlpath):
            doc = minidom.parse(xmlpath)
            for elem in doc.getElementsByTagName("dock"):
                if elem.getAttribute("id") == self.id:
                    for node in elem.childNodes:
                        elem.removeChild(node)
                    dockElem = elem
                    break
        
        if not dockElem:
            doc = minidom.getDOMImplementation().createDocument(None, "docks", None)
            dockElem = doc.createElement("dock")
            dockElem.setAttribute("id", self.id)
            doc.documentElement.appendChild(dockElem)
        
        if self.get_child():
            self.__addToXML(self.get_child(), dockElem, doc)
        f = open(xmlpath, "w")
        doc.writexml(f)
        f.close()
        doc.unlink()
    
    def __addToXML (self, component, parentElement, document):
        if isinstance(component, DockComposite):
            pos = component.paned.get_position()
            if component.getPosition() in (NORTH, SOUTH):
                childElement = document.createElement("v")
                size = float(component.get_allocation().height)
            else:
                childElement = document.createElement("h")
                size = float(component.get_allocation().width)
#             if component.getPosition() in (NORTH, SOUTH):
#                 print "saving v position as %s out of %s (%s)" % (str(pos), str(size), str(pos/max(size,pos)))
            childElement.setAttribute("pos", str(pos/max(size,pos)))
            self.__addToXML(component.getComponents()[0], childElement, document)
            self.__addToXML(component.getComponents()[1], childElement, document)
        
        elif isinstance(component, DockLeaf):
            childElement = document.createElement("leaf")
            childElement.setAttribute("current", component.getCurrentPanel())
            childElement.setAttribute("dockable", str(component.isDockable()))
            for panel, title, id in component.getPanels():
                e = document.createElement("panel")
                e.setAttribute("id", id)
                childElement.appendChild(e)
        
        parentElement.appendChild(childElement)
    
    def loadFromXML (self, xmlpath, idToWidget):
        doc = minidom.parse(xmlpath)
        for elem in doc.getElementsByTagName("dock"):
            if elem.getAttribute("id") == self.id:
                break
        else:
            raise AttributeError("XML file contains no <dock> elements with id '%s'" % self.id)
        
        child = [n for n in elem.childNodes if isinstance(n, minidom.Element)]
        if child:
            self.addComponent(self.__createWidgetFromXML(child[0], idToWidget)) 
    
    def __createWidgetFromXML (self, parentElement, idToWidget):
        children = [n for n in parentElement.childNodes
                      if isinstance(n, minidom.Element)]
        
        if parentElement.tagName in ("h", "v"):
            child1, child2 = children
            if parentElement.tagName == "h":
                new = PyDockComposite(EAST)
            else: new = PyDockComposite(SOUTH)
            new.initChildren(self.__createWidgetFromXML(child1, idToWidget),
                             self.__createWidgetFromXML(child2, idToWidget),
                             preserve_dimensions=True)
            def cb (widget, event, pos):
                allocation = widget.get_allocation()
                if parentElement.tagName == "h":
                    widget.set_position(int(allocation.width * pos))
                else:
#                     print "loading v position as %s out of %s (%s)" % \
#                     (int(allocation.height * pos), str(allocation.height), str(pos))
                    widget.set_position(int(allocation.height * pos))
                widget.disconnect(conid)
            conid = new.paned.connect("size-allocate", cb,
                                      float(parentElement.getAttribute("pos")))
            return new
        
        elif parentElement.tagName == "leaf":
            id = children[0].getAttribute("id")
            title, widget = idToWidget[id]
            leaf = PyDockLeaf(widget, title, id)
            for panelElement in children[1:]:
                id = panelElement.getAttribute("id")
                title, widget = idToWidget[id]
                leaf.dock(widget, CENTER, title, id)
            leaf.setCurrentPanel(parentElement.getAttribute("current"))
            if parentElement.getAttribute("dockable").lower() == "false":
                leaf.setDockable(False)
            return leaf
