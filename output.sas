begin_version
3
end_version
begin_metric
0
end_metric
31
begin_variable
var0
-1
2
Atom pole_empty(gear2)
NegatedAtom pole_empty(gear2)
end_variable
begin_variable
var1
-1
2
Atom pole_empty(pole1)
NegatedAtom pole_empty(pole1)
end_variable
begin_variable
var2
-1
2
Atom pole_empty(pole2)
NegatedAtom pole_empty(pole2)
end_variable
begin_variable
var3
-1
2
Atom pole_have_things(gear2, p0)
NegatedAtom pole_have_things(gear2, p0)
end_variable
begin_variable
var4
-1
2
Atom pole_have_things(gear2, p1)
NegatedAtom pole_have_things(gear2, p1)
end_variable
begin_variable
var5
-1
2
Atom pole_have_things(gear2, p2)
NegatedAtom pole_have_things(gear2, p2)
end_variable
begin_variable
var6
-1
2
Atom pole_have_things(pole1, p0)
NegatedAtom pole_have_things(pole1, p0)
end_variable
begin_variable
var7
-1
2
Atom pole_have_things(pole1, p1)
NegatedAtom pole_have_things(pole1, p1)
end_variable
begin_variable
var8
-1
2
Atom pole_have_things(pole1, p2)
NegatedAtom pole_have_things(pole1, p2)
end_variable
begin_variable
var9
-1
2
Atom pole_have_things(pole2, p0)
NegatedAtom pole_have_things(pole2, p0)
end_variable
begin_variable
var10
-1
2
Atom pole_have_things(pole2, p1)
NegatedAtom pole_have_things(pole2, p1)
end_variable
begin_variable
var11
-1
2
Atom pole_have_things(pole2, p2)
NegatedAtom pole_have_things(pole2, p2)
end_variable
begin_variable
var12
-1
2
Atom pole_position(gear1, slot10)
Atom pole_position(gear1, slot3)
end_variable
begin_variable
var13
-1
2
Atom pole_position(gear2, slot1)
Atom pole_position(gear2, slot12)
end_variable
begin_variable
var14
-1
3
Atom pole_position(pole1, slot1)
Atom pole_position(pole1, slot2)
Atom pole_position(pole1, slot3)
end_variable
begin_variable
var15
-1
3
Atom pole_position(pole2, slot10)
Atom pole_position(pole2, slot11)
Atom pole_position(pole2, slot12)
end_variable
begin_variable
var16
-1
2
Atom pole_start_moving(pole1)
Atom pole_stop_moving(pole1)
end_variable
begin_variable
var17
-1
2
Atom pole_start_moving(pole2)
Atom pole_stop_moving(pole2)
end_variable
begin_variable
var18
-1
3
Atom product_at(p0, slot1)
Atom product_at(p0, slot12)
<none of those>
end_variable
begin_variable
var19
-1
3
Atom product_at(p1, slot1)
Atom product_at(p1, slot12)
<none of those>
end_variable
begin_variable
var20
-1
3
Atom product_at(p2, slot1)
Atom product_at(p2, slot12)
<none of those>
end_variable
begin_variable
var21
-1
2
Atom slot_have_pole(slot1)
NegatedAtom slot_have_pole(slot1)
end_variable
begin_variable
var22
-1
2
Atom slot_have_pole(slot10)
NegatedAtom slot_have_pole(slot10)
end_variable
begin_variable
var23
-1
2
Atom slot_have_pole(slot11)
NegatedAtom slot_have_pole(slot11)
end_variable
begin_variable
var24
-1
2
Atom slot_have_pole(slot12)
NegatedAtom slot_have_pole(slot12)
end_variable
begin_variable
var25
-1
2
Atom slot_have_pole(slot2)
NegatedAtom slot_have_pole(slot2)
end_variable
begin_variable
var26
-1
2
Atom slot_have_pole(slot3)
NegatedAtom slot_have_pole(slot3)
end_variable
begin_variable
var27
-1
2
Atom slot_not_available(slot1)
NegatedAtom slot_not_available(slot1)
end_variable
begin_variable
var28
-1
2
Atom slot_not_available(slot10)
NegatedAtom slot_not_available(slot10)
end_variable
begin_variable
var29
-1
2
Atom slot_not_available(slot12)
NegatedAtom slot_not_available(slot12)
end_variable
begin_variable
var30
-1
2
Atom slot_not_available(slot3)
NegatedAtom slot_not_available(slot3)
end_variable
9
begin_mutex_group
2
12 0
12 1
end_mutex_group
begin_mutex_group
2
13 0
13 1
end_mutex_group
begin_mutex_group
3
14 0
14 1
14 2
end_mutex_group
begin_mutex_group
3
15 0
15 1
15 2
end_mutex_group
begin_mutex_group
2
16 0
16 1
end_mutex_group
begin_mutex_group
2
17 0
17 1
end_mutex_group
begin_mutex_group
2
18 0
18 1
end_mutex_group
begin_mutex_group
2
19 0
19 1
end_mutex_group
begin_mutex_group
2
20 0
20 1
end_mutex_group
begin_state
1
0
0
0
1
1
1
1
1
1
1
1
1
1
2
2
1
1
1
0
0
1
1
1
0
1
0
1
0
0
1
end_state
begin_goal
1
18 0
end_goal
32
begin_operator
do-hangup-pole-exchanging gear2 pole2 slot12 p0
2
13 1
15 2
6
0 0 0 1
0 2 1 0
0 3 -1 0
0 9 -1 1
0 18 1 2
0 29 0 1
1
end_operator
begin_operator
do-hangup-pole-exchanging gear2 pole2 slot12 p1
2
13 1
15 2
6
0 0 0 1
0 2 1 0
0 4 -1 0
0 10 -1 1
0 19 1 2
0 29 0 1
1
end_operator
begin_operator
do-hangup-pole-exchanging gear2 pole2 slot12 p2
2
13 1
15 2
6
0 0 0 1
0 2 1 0
0 5 -1 0
0 11 -1 1
0 20 1 2
0 29 0 1
1
end_operator
begin_operator
do-hangup-pole-exchanging pole2 gear2 slot12 p0
2
13 1
15 2
6
0 0 1 0
0 2 0 1
0 3 -1 1
0 9 -1 0
0 18 1 2
0 29 0 1
1
end_operator
begin_operator
do-hangup-pole-exchanging pole2 gear2 slot12 p1
2
13 1
15 2
6
0 0 1 0
0 2 0 1
0 4 -1 1
0 10 -1 0
0 19 1 2
0 29 0 1
1
end_operator
begin_operator
do-hangup-pole-exchanging pole2 gear2 slot12 p2
2
13 1
15 2
6
0 0 1 0
0 2 0 1
0 5 -1 1
0 11 -1 0
0 20 1 2
0 29 0 1
1
end_operator
begin_operator
do-hangup-pole-stocking gear2 slot1 p0
1
13 0
3
0 0 0 1
0 3 -1 0
0 18 0 2
1
end_operator
begin_operator
do-hangup-pole-stocking gear2 slot1 p1
1
13 0
3
0 0 0 1
0 4 -1 0
0 19 0 2
1
end_operator
begin_operator
do-hangup-pole-stocking gear2 slot1 p2
1
13 0
3
0 0 0 1
0 5 -1 0
0 20 0 2
1
end_operator
begin_operator
do-hangup-pole-stocking pole1 slot1 p0
1
14 0
3
0 1 0 1
0 6 -1 0
0 18 0 2
1
end_operator
begin_operator
do-hangup-pole-stocking pole1 slot1 p1
1
14 0
3
0 1 0 1
0 7 -1 0
0 19 0 2
1
end_operator
begin_operator
do-hangup-pole-stocking pole1 slot1 p2
1
14 0
3
0 1 0 1
0 8 -1 0
0 20 0 2
1
end_operator
begin_operator
do-move-gear-empty gear1 slot10 slot3
0
3
0 12 0 1
0 28 -1 0
0 30 0 1
1
end_operator
begin_operator
do-move-gear-empty gear1 slot3 slot10
0
3
0 12 1 0
0 28 0 1
0 30 -1 0
1
end_operator
begin_operator
do-move-gear-empty gear2 slot1 slot12
1
0 0
3
0 13 0 1
0 27 -1 0
0 29 0 1
1
end_operator
begin_operator
do-move-gear-empty gear2 slot12 slot1
1
0 0
3
0 13 1 0
0 27 0 1
0 29 -1 0
1
end_operator
begin_operator
do-move-gear-equip gear2 slot1 slot12 p0
2
0 1
27 0
3
0 13 0 1
0 18 0 1
0 29 -1 0
1
end_operator
begin_operator
do-move-gear-equip gear2 slot1 slot12 p1
2
0 1
27 0
3
0 13 0 1
0 19 0 1
0 29 -1 0
1
end_operator
begin_operator
do-move-gear-equip gear2 slot1 slot12 p2
2
0 1
27 0
3
0 13 0 1
0 20 0 1
0 29 -1 0
1
end_operator
begin_operator
do-move-gear-equip gear2 slot12 slot1 p0
2
0 1
29 0
3
0 13 1 0
0 18 1 0
0 27 -1 0
1
end_operator
begin_operator
do-move-gear-equip gear2 slot12 slot1 p1
2
0 1
29 0
3
0 13 1 0
0 19 1 0
0 27 -1 0
1
end_operator
begin_operator
do-move-gear-equip gear2 slot12 slot1 p2
2
0 1
29 0
3
0 13 1 0
0 20 1 0
0 27 -1 0
1
end_operator
begin_operator
do-move-pole-forward-1 pole1 slot1 slot2
1
16 0
3
0 14 0 1
0 21 0 1
0 25 1 0
1
end_operator
begin_operator
do-move-pole-forward-1 pole1 slot2 slot3
1
16 0
3
0 14 1 2
0 25 0 1
0 26 1 0
1
end_operator
begin_operator
do-move-pole-forward-1 pole2 slot10 slot11
1
17 0
3
0 15 0 1
0 22 0 1
0 23 1 0
1
end_operator
begin_operator
do-move-pole-forward-1 pole2 slot11 slot12
1
17 0
3
0 15 1 2
0 23 0 1
0 24 1 0
1
end_operator
begin_operator
do-move-pole-inverse-1 pole1 slot2 slot1
1
16 0
3
0 14 1 0
0 21 1 0
0 25 0 1
1
end_operator
begin_operator
do-move-pole-inverse-1 pole1 slot3 slot2
1
16 0
3
0 14 2 1
0 25 1 0
0 26 0 1
1
end_operator
begin_operator
do-move-pole-inverse-1 pole2 slot11 slot10
1
17 0
3
0 15 1 0
0 22 1 0
0 23 0 1
1
end_operator
begin_operator
do-move-pole-inverse-1 pole2 slot12 slot11
1
17 0
3
0 15 2 1
0 23 1 0
0 24 0 1
1
end_operator
begin_operator
do-start-moving-pole pole1
0
1
0 16 1 0
1
end_operator
begin_operator
do-start-moving-pole pole2
0
1
0 17 1 0
1
end_operator
0
