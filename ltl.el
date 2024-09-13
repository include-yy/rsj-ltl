;; -*- lexical-binding: t; mode: lisp-interaction-*-

(package-activate-all)

(require 'peg)
(require 'queue)

(defvar ltl/base-dir default-directory
  "default directory of this project.")
(defvar ltl/exe-path (file-name-concat ltl/base-dir "ltl2ba-1.3/ltl2ba")
  "executable file's path of ltl2ba")

(defun ltl-call-ltl2ba (str)
  (shell-command-to-string (concat ltl/exe-path " " "-f " (format "'%s'" str))))

(defun ltl-buchi2list ()
  (peg-parse
   (translation_unit "never" _  statements)
   (statements "{" (+ _ statement _)"}")
   (statement state _ ":" _
	      (or (and "if" (list (+ transform)) "fi;")
		  (list "skip"))
	      `(state arrows -- (list state arrows)))
   (state (substring [a-z A-Z] (* [a-z A-Z 0-9 "_"])))
   (transform (list _ "::" _ condition _ "->" _ "goto" _ state _))
   (condition (or (and "(1)" `(-- (list "1")))
		  (list (and "("_ id _ id-list _")"))))
   (id-list (* _ "&&" _ id))
   (id (substring (opt "!") identifier))
   (identifier [a-z A-Z] (* [a-z A-Z 0-9 "_"]))
   (_ (* (or [" \n\t"] comment)))
   (comment "/*" (* (not (or "\n" (eob))) (any)))))

(defun ltl-sexp2ltl (sexp)
    (cond
     ((atom sexp)
      (cond
       ((eq sexp 'ture) "true")
       ((eq sexp 'false) "false")
       ((keywordp sexp) (substring (symbol-name sexp) 1))
       (t (error "not a valid logicproposition"))))
     ((listp sexp)
      (let ((op (pcase (car sexp)
		  ('not "!") ('-> "->") ('<-> "<->")
		  ('and "and") ('or "or")
		  ('G "[]") ('F "<>") ('U "U") ('V "V")
		  ('X "X")
		  (_ (error "invalid operator")))))
	(cond
	 ((member op '("!" "[]" "<>" "U" "V" "X"))
	  (if (= (length sexp) 2)
	      (format "(%s %s)" op (ltl-sexp2ltl (cadr sexp)))
	    (error "these op just allows one operand")))
	 ((member op '("->" "<->"))
	  (if (= (length sexp) 3)
	      (format "(%s %s %s)"
		      (ltl-sexp2ltl (cadr sexp)) op
		      (ltl-sexp2ltl (caddr sexp)))
	    (error "these op just allow two operand")))
	 (t (let ((ltls (mapcar #'ltl-sexp2ltl (cdr sexp))))
	      (if (< (length ltls) 2)
		  (error "'and' and 'or' accept two or more operands")
		(concat "(" (car ltls) " "
			(if (equal op "and")
			    (mapconcat (lambda (x) (concat "&& " x))
				       (cdr ltls) " ")
			  (mapconcat (lambda (x) (concat "|| " x))
				     (cdr ltls) " "))
			")")))))))))

(defun ltl-ltl2ba (sexp)
  (let* ((formula (ltl-sexp2ltl sexp))
	 (automaton (ltl-call-ltl2ba formula)))
    (with-temp-buffer
      (insert automaton)
      (goto-char (point-min))
      (ltl-buchi2list))))

(ltl-sexp2ltl '(and (F :a1) (F :a2) (F :a3)))
"((<> a1) && (<> a2) && (<> a3))"

;; (ltl-ltl2ba '(and (F :a1) (F :a2) (F :a3)))

(defun ltl-ba-opt (ba-list)
  "do some optimization"
  (mapcar
   (lambda (b)
     (let* ((state-name (car b))
	    (states (cadr b)))
       (list state-name
	     (cl-remove-if
	      (lambda (x)
		(let* ((variables (car x))
		       (next-state (cadr x)))
		  (when (or (equal (car variables) "1")
			    (> (length variables) 1))
		    t)))
	      states))))
   ba-list))

;; (ltl-ba-opt
;;  '(("accept_all" nil) ("T2_S7" ((("1") "T2_S7") (("a3") "accept_all"))) ("T1_S6" ((("1") "T1_S6") (("a2") "accept_all"))) ("T1_S5" ((("1") "T1_S5") (("a3") "T1_S6") (("a2") "T2_S7") (("a2" "a3") "accept_all"))) ("T0_S4" ((("1") "T0_S4") (("a1") "accept_all"))) ("T0_S3" ((("1") "T0_S3") (("a3") "T0_S4") (("a1") "T2_S7") (("a1" "a3") "accept_all"))) ("T0_S2" ((("1") "T0_S2") (("a2") "T0_S4") (("a1") "T1_S6") (("a1" "a2") "accept_all"))) ("T0_init" ((("1") "T0_init") (("a3") "T0_S2") (("a2") "T0_S3") (("a2" "a3") "T0_S4") (("a1") "T1_S5") (("a1" "a3") "T1_S6") (("a1" "a2") "T2_S7") (("a1" "a2" "a3") "accept_all")))))

;; (("accept_all" nil) ("T2_S7" ((("a3") "accept_all"))) ("T1_S6" ((("a2") "accept_all"))) ("T1_S5" ((("a3") "T1_S6") (("a2") "T2_S7"))) ("T0_S4" ((("a1") "accept_all"))) ("T0_S3" ((("a3") "T0_S4") (("a1") "T2_S7"))) ("T0_S2" ((("a2") "T0_S4") (("a1") "T1_S6"))) ("T0_init" ((("a3") "T0_S2") (("a2") "T0_S3") (("a1") "T1_S5"))))

(defun ltl-ba-get-states (ba-list)
  (mapcar #'car ba-list))

(defun ltl-ba-get-variables (ba-list)
  (cl-delete-duplicates
     (apply 'append
	 (mapcar (lambda (x)
		   (let* ((trs (cadr x)))
		     (mapcar #'caar trs)))
		 ba-list))
  :test #'equal))

;; (ltl-ba-get-variables '(("accept_all" nil) ("T2_S7" ((("a3") "accept_all"))) ("T1_S6" ((("a2") "accept_all"))) ("T1_S5" ((("a3") "T1_S6") (("a2") "T2_S7"))) ("T0_S4" ((("a1") "accept_all"))) ("T0_S3" ((("a3") "T0_S4") (("a1") "T2_S7"))) ("T0_S2" ((("a2") "T0_S4") (("a1") "T1_S6"))) ("T0_init" ((("a3") "T0_S2") (("a2") "T0_S3") (("a1") "T1_S5")))))
;; ("a3" "a2" "a1")

;; (ltl-ba-get-states '(("accept_all" nil) ("T2_S7" ((("a3") "accept_all"))) ("T1_S6" ((("a2") "accept_all"))) ("T1_S5" ((("a3") "T1_S6") (("a2") "T2_S7"))) ("T0_S4" ((("a1") "accept_all"))) ("T0_S3" ((("a3") "T0_S4") (("a1") "T2_S7"))) ("T0_S2" ((("a2") "T0_S4") (("a1") "T1_S6"))) ("T0_init" ((("a3") "T0_S2") (("a2") "T0_S3") (("a1") "T1_S5")))))
;; ("accept_all" "T2_S7" "T1_S6" "T1_S5" "T0_S4" "T0_S3" "T0_S2" "T0_init")


(defun ltl-dijkstra (ba-graph cost-hash point)
  (let* ((vertex (ltl-ba-get-states ba-graph))
	 (variables (ltl-ba-get-variables ba-graph))
	 (dist-hash (let ((h (make-hash-table :test 'equal)))
		      (dolist (v vertex)
			(puthash v 1.0e+INF h))
		      (puthash "T0_init" 0 h)
		      h))
	 (predecessors (let ((h (make-hash-table :test 'equal)))
			 (dolist (v vertex h)
			   (puthash v nil h))))
	 (priority-queue (let ((q (make-queue)))
			   (queue-enqueue q (list 0 point "T0_init"))
			   q)))
    (while (not (queue-empty priority-queue))
      (let* ((current (queue-dequeue priority-queue))
	     (curr-dist (nth 0 current))
	     (curr-point (nth 1 current))
	     (curr-vertex (nth 2 current)))
	(unless (> curr-dist (gethash curr-vertex dist-hash))
	  (let* ((arrows (cadr (assoc curr-vertex ba-graph))))
	    (dolist (a arrows)
	      (let* ((new-point (caar a))
		     (weight (gethash (list curr-point new-point) cost-hash))
		     (next-state (cadr a))
		     (dist (+ curr-dist weight)))
		(when (< dist (gethash next-state dist-hash))
		  (puthash next-state dist dist-hash)
		  ;;(puthash next-state new-point predecessors)
		  ;;(push new-point (gethash next-state predecessors))
		  (setf (gethash next-state predecessors)
			(cons new-point (gethash curr-vertex predecessors)))
		  (queue-enqueue priority-queue
				 (list dist new-point next-state)))))))))
    (list dist-hash predecessors)))

(defun ltl-getpath (ba-graph cost-hash)
  (let ((res (ltl-dijkstra ba-graph cost-hash "0")))
    (let ((dh (car res))
	  (path (cadr res)))
      (list (reverse (gethash "accept_all" path))
	    (gethash "accept_all" dh)))))

(defun ltl-make-cost-hash (dlist)
  (let ((h (make-hash-table :test 'equal)))
    (dolist (d dlist h)
      (let* ((p1 (nth 0 d))
	     (p2 (nth 1 d))
	     (dist (nth 2 d)))
	(puthash (list p1 p2) dist h)
	(puthash (list p2 p1) dist h)
	(puthash (list p1 p1) 0.0 h)
	(puthash (list p2 p2) 0.0 h)))))

;; (setq a '(("accept_all" nil) ("T2_S7" ((("a3") "accept_all"))) ("T1_S6" ((("a2") "accept_all"))) ("T1_S5" ((("a3") "T1_S6") (("a2") "T2_S7"))) ("T0_S4" ((("a1") "accept_all"))) ("T0_S3" ((("a3") "T0_S4") (("a1") "T2_S7"))) ("T0_S2" ((("a2") "T0_S4") (("a1") "T1_S6"))) ("T0_init" ((("a3") "T0_S2") (("a2") "T0_S3") (("a1") "T1_S5")))))

;; (setq b (ltl-make-cost-hash '(("a1" "a2" 2) ("a2" "a3" 4) ("a1" "a3" 3) ("0" "a1" 1) ("0" "a2" 2) ("0" "a3" 3))))

;; (ltl-getpath a b)
;; (("a1" "a2" "a3") 7)

;;; process

;; (ltl-ltl2ba '(and (F :a1) (F :a2) (F :a3)))
;; (ltl-ba-opt res)
;; (ltl-make-cost-hash ...)
;; (ltl-getpath graph cost-hash)
;; (("a1" "a2" "a3") 7)

(defun ltl-doit (sexp dist)
  (let* ((ba (ltl-ltl2ba sexp))
	 (good-ba (ltl-ba-opt ba))
	 (cost-hash (ltl-make-cost-hash dist))
	 (result (ltl-getpath good-ba cost-hash)))
    (print result)))

;; emacs --batch -l "ltl.el"  --eval "(ltl-doit '(and (F :a1) (F :a2) (F :a3)) '((\"a1\" \"a2\" 2) (\"a2\" \"a3\" 4) (\"a1\" \"a3\" 3) (\"0\" \"a1\" 1) (\"0\" \"a2\" 2) (\"0\" \"a3\" 3)))"

;; (ltl-sexp2ltl '(and (F :a1)
;; 		    (X (and (F :a2)
;; 			    (X (and (F :a3)
;; 				    (X (and (F :a2)
;; 					    (X (F :a1))))))))))
;; (ltl-ltl2ba '(and (F :a1)
;; 		    (X (and (F :a2)
;; 			    (X (and (F :a3)
;; 				    (X (and (F :a2)
;; 					    (X (F :a1))))))))))

;; (and (F :a1) (X (and (F :a2) (X (and (F :a3) (X (and (F :a2) (X (F :a1)))))))))

;; a1 = Q([S('and'), [S('F'), S(':a5')], [S('X'), [S('and'), [S('F'), S(':a4')], [S('X'), [S('and'), [S('F'), S(':a3')], [S('X'), [S('and'), [S('F'), S(':a2')], [S('X'), [S('F'), S(':a1')]]]]]]]]])
