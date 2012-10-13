#!/usr/bin/env python
#-*- coding:utf-8 -*-
# Copyright (C) 
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# 
#
# @file lc_dict.py
# @brief a simple cn-en dict.
# @author Long Changjin <admin@longchangjin.cn>
# @version 0.1
# @date 2012-10-12


import urllib
import json
import gtk
import threading
import os

gtk.gdk.threads_init()

def translate(url):
    try:
        u = urllib.urlopen(url)
        con = u.read()
    except Exception, e:
        print e
        u.close()
        return None
    u.close()
    try:
        back = json.loads(con)
        return back
    except:
        return None

class Youdao(object):
    '''youdao api'''
    def __init__(self, text_buffer):
        KEYFROM = 'LongChang-blog'
        KEY = '1548662058'
        self.URL = "http://fanyi.youdao.com/openapi.do?keyfrom=%s&key=%s&type=data&doctype=json&version=1.1&q=" % (KEYFROM, KEY)
        self.text_buffer = text_buffer
    
    def trans(self, word):
        back = translate(self.URL + word)
        if back is None:
            error_msg = "网络错误！"
            return (False, error_msg)
        if back['errorCode'] != 0:
            if back['errorCode'] == 20:
                error_msg = "输入的文本过长"
            if back['errorCode'] == 30:
                error_msg = "无法进行有效的翻译"
            if back['errorCode'] == 40:
                error_msg = "不支持的语言类型"
            if back['errorCode'] == 50:
                error_msg = "无效的key"
            return (False, error_msg)
        return (True, back)
    
    def parse(self, back):
        if back is None:
            return
        self.text_buffer.delete(*self.text_buffer.get_bounds())
        insert_iter = self.text_buffer.get_iter_at_mark(self.text_buffer.get_insert())
        self.text_buffer.insert_with_tags_by_name(insert_iter, "有道翻译", "title")
        con = '\n'
        i = 1
        for c in back['translation']: # 有道翻译
            con += "%d. %s\n" % (i, c)
            i += 1
        self.text_buffer.insert_with_tags_by_name(insert_iter, con, "content")
        if "basic" in back:           # 有道词典-基本词典
            con = ''
            self.text_buffer.insert_with_tags_by_name(insert_iter, "\n有道词典\n", "title")
            if "phonetic" in back["basic"]:
                self.text_buffer.insert_with_tags_by_name(insert_iter, "%s\n" % back["basic"]["phonetic"], "content")
            i = 1
            for c in back['basic']['explains']:
                con += "%d. %s\n" % (i, c)
                i += 1
            self.text_buffer.insert_with_tags_by_name(insert_iter, con, "content")
        if "web" in back:             # 有道词典-网络释义
            con = '\n'
            self.text_buffer.insert_with_tags_by_name(insert_iter, "\n网络释义", "title")
            n = 1
            for explains in back['web']:
                con += "原文%d：%s\n" % (n, explains['key'])
                n += 1
                i = 1
                for c in explains['value']:
                    con += "%d. %s\n" % (i, c)
                    i += 1
            self.text_buffer.insert_with_tags_by_name(insert_iter, con, "content")

class Baidu(object):
    '''baidu api'''
    def __init__(self, text_buffer):
        KEY = "V2MA11RGHvr0d43tqH471NKi"
        self.URL = "http://openapi.baidu.com/public/2.0/bmt/translate?client_id=%s&from=auto&to=auto&q=" % KEY
        self.text_buffer = text_buffer
    
    def trans(self, word):
        back = translate(self.URL + word)
        if back is None:
            error_msg = "网络错误！"
            return (False, error_msg)
        if "error_code" in back:
            if back['error_code'] == "52001":
                error_msg = "连接超时"
            if back['error_code'] == "52002":
                error_msg = "翻译系统错误"
            if back['error_code'] == "52003":
                error_msg = "未授权的用户"
            return (False, error_msg)
        return (True, back)
    
    def parse(self, back):
        if back is None:
            return
        self.text_buffer.delete(*self.text_buffer.get_bounds())
        insert_iter = self.text_buffer.get_iter_at_mark(self.text_buffer.get_insert())
        self.text_buffer.insert_with_tags_by_name(insert_iter, "百度翻译", "title")
        con = '\n%s->%s\n' % (back['from'], back['to'])
        i = 1
        for t in back['trans_result']: # 百度翻译
            con += "%d.原文：%s\n  译文：%s\n" % (i, t['src'], t['dst'])
            i += 1
        self.text_buffer.insert_with_tags_by_name(insert_iter, con, "content")
        
class Dict(object):
    '''dict'''
    def __init__(self):
        self.win = gtk.Window()
        self.win.connect("delete-event", self.hide_window)
        self.win.set_resizable(False)
        self.win.set_title("一个简单的词典 -- 龙昌")
        self.win.set_size_request(500, 250)
        self.win.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        ico = gtk.status_icon_new_from_file(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "book.png"))
        #ico.set_has_tooltip(True)
        #ico.set_tooltip_text("点击显示/隐藏窗口")
        ico.connect("popup-menu", self.right_button_click)
        ico.connect("activate", self.tray_activate)

        self.search_combo = gtk.combo_box_new_text()
        self.search_combo.append_text('youdao')
        self.search_combo.append_text('baidu')
        self.search_combo.set_active(0)

        search_hbox = gtk.HBox(False, 4)
        self.search_entry = gtk.Entry()
        self.search_button = gtk.Button("翻译")

        search_hbox.pack_start(self.search_entry, True, True)
        search_hbox.pack_start(self.search_combo, False, False)
        search_hbox.pack_start(self.search_button, False, False)

        scroll_win = gtk.ScrolledWindow()
        scroll_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.result_text = gtk.TextView()
        self.result_text.set_editable(False)
        scroll_win.add(self.result_text)
        self.text_buffer = self.result_text.get_buffer()
        tag_table = self.text_buffer.get_tag_table()
        title_tag = gtk.TextTag('title')
        title_tag.set_property("size", 17*1024)
        title_tag.set_property("foreground", "#FF0000")
        title_tag.set_property("weight-set", True)

        content_tag = gtk.TextTag('content')
        content_tag.set_property("size", 11*1024)
        tag_table.add(title_tag)
        tag_table.add(content_tag)

        self.main_vbox = gtk.VBox(False, 5)
        self.main_vbox.pack_start(search_hbox, False, False)
        self.main_vbox.pack_start(scroll_win, True, True)

        vbox = gtk.VBox(False)
        self.statusbar = gtk.Statusbar()
        status_box = self.statusbar.get_message_area()
        status_box.pack_start(gtk.Label("作者：龙昌  http://www.xefan.com  "), False, False)
        self.status_id = self.statusbar.get_context_id("operate")
        self.statusbar.push(self.status_id, "简单词典工具")
        vbox.pack_start(self.main_vbox, True, True)
        vbox.pack_start(self.statusbar, False, False)

        accel_group = gtk.AccelGroup()
        self.win.add_accel_group(accel_group)
        key, mod = gtk.accelerator_parse("<Enter>")
        # 设置按下回车进行查询
        self.search_button.add_accelerator("clicked", accel_group, gtk.keysyms.Return, 0, gtk.ACCEL_VISIBLE)
        self.search_button.add_accelerator("clicked", accel_group, gtk.keysyms.KP_Enter, 0, gtk.ACCEL_VISIBLE)
        self.search_button.connect("clicked", self.search_word, self.search_entry)

        self.win.add(vbox)
        self.win.show_all()

        self.dicts = {
            "youdao" : Youdao(self.text_buffer),
            "baidu"  : Baidu(self.text_buffer)}
        gtk.main()

    def search_word(self, button, entry):
        text = entry.get_text()
        if text.strip() == '':
            d = gtk.MessageDialog(self.win, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, "要翻译的词为空！")
            d.run()
            d.destroy()
            return
        #button.set_label("翻译中...")
        self.statusbar.pop(self.status_id)
        self.statusbar.push(self.status_id, "翻译中...")
        self.main_vbox.set_sensitive(False)
        t = threading.Thread(target=self.search_word_thread, args=(text, ))
        t.setDaemon(True)
        t.start()

    def search_word_thread(self, text):
        dst = self.dicts[self.search_combo.get_active_text()].trans(text)
        gtk.gdk.threads_enter()
        if not dst[0]:
            self.statusbar.pop(self.status_id)
            self.statusbar.push(self.status_id, "错误：%s" % dst[1])
            d = gtk.MessageDialog(self.win, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, dst[1])
            d.run()
            d.destroy()
        else:
            self.statusbar.pop(self.status_id)
            self.statusbar.push(self.status_id, "翻译完成")
            self.dicts[self.search_combo.get_active_text()].parse(dst[1])
        self.search_over()
        gtk.gdk.threads_leave()

    def search_over(self):
        self.main_vbox.set_sensitive(True)
        self.search_button.set_label("翻译")
        self.search_entry.grab_focus()

    def hide_window(self, win, event):
        win.hide_all()
        return True

    def tray_activate(self, tray_ico):
        if self.win.get_visible():
            self.win.hide_all()
        else:
            self.win.show_all()

    def right_button_click(self, status_ico, button, time):
        menu = gtk.Menu()
        if self.win.get_visible():
            operate = gtk.MenuItem("隐藏")
        else:
            operate = gtk.MenuItem("显示")
        operate.connect("activate", lambda w: self.tray_activate(None))
        quit = gtk.MenuItem("退出")
        quit.connect("activate", gtk.main_quit)
        menu.connect("selection-done", lambda m: m.destroy())
        menu.append(operate)
        menu.append(quit)
        menu.show_all()
        menu.popup(None, None, gtk.status_icon_position_menu, button, time, status_ico)


if __name__ == '__main__':
    Dict()
