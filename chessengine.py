#
#    Ceibal Chess - A chess activity for Sugar.
#    Copyright (C) 2008, 2009 Alejandro Segovia <asegovi@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#

import os
import sys
from subprocess import Popen, PIPE
from piece import Move
from errors import IAError

import logging
log = logging.getLogger()

class GnuChessEngine:
        '''GNU Chess wrapper class.'''
        def __init__(self):
                '''Create a new instance of the GNU Chess wrapper, locate the
                gnuchess executable, open a pipe to it and setup the comm.'''
                try:
                        path = os.path.join(os.environ["SUGAR_BUNDLE_PATH"],"engines")
                        if not "Ajedrez.activity" in path:
                                print "Runningn ceibal-chess from Terminal or some other place"
                                path = os.path.join("", "engines")
                except:
                        path = os.path.join(".", "engines")

                self.plat = sys.platform
                if  self.plat == "linux2":
                        engine_exec = "gnuchess-linux"
                elif self.plat == "darwin":
                        engine_exec = "gnuchess-osx"
                elif self.plat == "win32":
                        engine_exec = "gnuchess-win32.exe"
                else:
                        log.warn("No gnuchess for %s, using system default", plat)
                        engine_exec = ""

                if engine_exec != "":
                        engine_path = os.path.join(path, engine_exec)
                else:
                        log.info("Trying to find gnuchess in PATH")
                        engine_path = "gnuchess"

                #Check whether the engine is executable:
                if not os.access(engine_path.split()[0], os.X_OK):
                        log.error("Engine is not executable, try: chmod +x %s",
                                          engine_path.split()[0])
                        raise IOError("Chess engine is not executable.")

                args = [engine_exec, '-e', '-x']

                try:
                        if self.plat == "win32":
                                self.proc = Popen(args, executable=os.path.abspath(engine_path), stdin=PIPE, stdout=PIPE)
                        else:
                                self.proc = Popen(args, executable=os.path.abspath(engine_path), stdin=PIPE, stdout=PIPE, close_fds=True)
                        self.fin = self.proc.stdout
                        self.fout = self.proc.stdin
                        
			#Check pipe:
                        self.fout.write("\n")
                        self.fout.flush()
                        self.fin.readline()
                        self.fin.readline()
                        self.fin.readline()
                        self.fout.write("depth 1\n")
                except Exception, ex:
			print ex
                        self.close()
                        raise

        def undo(self):
                # undo ai move
                self.fout.write('undo\n')
                # undo player move
                self.fout.write('undo\n')
                self.fout.flush()

        def move(self, move, controller):
                '''Write a player's move to GNU Chess. Return the engine's move.'''
                move_str = self.move_to_gnuchess(move)

                log.debug("Calling GNU Chess with move: %s", move_str)

                self.fout.write(move_str + "\n")
                self.fout.flush()
                l = self.fin.readline()
                while l.find("My move is") == -1:
                        if l.find("Illegal move") != -1:
                                raise IAError( \
                                        "Player performed an illegal move: (%s), move was: %s" %
                                                (l, move_str))
                        l = self.fin.readline()
                ans = l.split()[3]
                log.debug("got answer from gnuchess '%s'", l)

                chess_ans = None
                type = None

                if len(ans) == 4:
                        chess_ans = (self.gnuchess_to_coords(ans[:2]), \
                                                self.gnuchess_to_coords(ans[2:]))
                elif len(ans) == 5:
                        chess_ans = (self.gnuchess_to_coords(ans[:2]), \
                                                self.gnuchess_to_coords(ans[2:4]))
                        type = ans[4].upper()
                else:
                        raise IAError("Unknown answer from gnuchess: %s" % (ans))

                controller.move(controller.board.black, chess_ans[0], chess_ans[1], type=type)

        def close(self):
                try:
                        if self.fout:
                                self.fout.write("quit\n")
                                self.fout.flush()
                                self.fout.close()
                                self.fout = None
                        if self.fin:
                                self.fin.close()
                                self.fin = None
                finally:
                        if self.proc:
                                try:
                                        if self.plat == "win32":
                                                pass
                                                #os.system("taskkill /PID %s" %self.proc.pid)
                                                #FIXME: Add something to kill the process in Windows OS,
                                                #the os.system solution does not work.
                                        else:
                                                os.kill(self.proc.pid, 15)
                                except OSError:
                                        pass
                                self.proc.wait()
                                self.proc = None
       
        def move_to_gnuchess(self, move):
                return str(move)

        def gnuchess_to_coords(self, move):
                letters = ["a", "b", "c", "d", "e", "f", "g", "h"]
                c = letters.index(move[0])
                r = int(8 - int(move[1]))
                return (c,r)
               
        def assert_sync(self, board):
                '''
                Validate whether the AI's internal representation of the board
                matches our board.
               
                Raises IAError (games out of sync) on error, otherwise, just returns.
               
                This is rather expensive and should only be perfomed
                in debug mode.
                '''
                log.debug("Called IA.assert_sync...")
                try:
                        self.fout.write("show board\n")
                        self.fout.write("\n")
                        self.fout.flush()
                       
                        log.debug("read 1...")
                        self.fin.readline()
                       
                        log.debug("read 2...")
                        ai_turn = self.fin.readline().split(" ")[0]
                       
                        #if ai_turn != board.current_turn.name:
                        #       raise IAError("Turns out of sync!")
                       
                        line = ""
                        ai_row = []
                        while len(ai_row) < 8:
                                line = self.fin.readline().replace("\n", "").strip()
                                ai_row = line.split(" ")

                        for row in range(8):
                                log.debug("row %d: %s" % (row, line))

                                for col in range(8):
                                        ai_cell = ai_row[col]
                                        if ai_cell == ".":
                                                if not board[col, row].piece:
                                                        continue
                                                raise AIError( \
                                                        "Out of sync: AI thinks (%d, %d) should be empty" %
                                                                (col, row))                                            
                                       
                                        if ai_cell.upper() != board[col, row].piece.CODE:
                                                raise AIError("Out of sync: piece at (%d, %d) differs" %
                                                        (col, row))
                                       
                                        if ai_cell.islower() and board[col, row].piece.owner.name != "black":
                                                raise AIError("Out of sync: owner at (%d, %d) differs" %
                                                        (col, row))
                                       
                                        if ai_cell.isupper() and board[col, row].piece.owner.name != "white":
                                                raise AIError("Out of sync: owner at (%d, %d) differs" %
                                                        (col, row))
                               
                                if row < 7:
                                        line = self.fin.readline().replace("\n", "").strip()
                                        ai_row = line.split(" ")
                       
                        log.debug("read 10...")
                        self.fin.readline()


                        log.debug("read 11...")
                        self.fin.readline()
                       
                except IOError, err:
                        raise IAError("Could not talk to engine: %s" % err.message )

