(define (problem electroplating)
	(:domain Electroplating)
	(:objects
		slot1 - slot
		slot2 - slot
		slot3 - slot
		slot4 - slot
		slot5 - slot
		slot6 - slot
		slot7 - slot
		slot8 - slot
		slot9 - slot
		slot10 - slot
		slot11 - slot
		slot12 - slot
		slot13 - slot
		slot14 - slot
		slot15 - slot
		slot16 - slot
		slot17 - slot
		slot18 - slot
		slot19 - slot
		slot20 - slot
		slot21 - slot
		slot22 - slot
		slot23 - slot
		slot24 - slot
		slot25 - slot
		slot26 - slot
		slot27 - slot
		slot28 - slot
		slot29 - slot
		slot30 - slot
		slot31 - slot
		slot32 - slot
		slot33 - slot
		slot34 - slot
		slot35 - slot
		slot36 - slot
		slot37 - slot
		slot38 - slot
		slot39 - slot
		pole1 - pole
		pole2 - pole
		pole3 - pole
		p100000 - product
		p0 - product
		)
	(:init
		(forward_slot_connection slot31 slot32)
		(pole_empty pole3)
		(inverse_slot_connection slot25 slot24)
		(pole_region pole2 slot16)
		(forward_slot_connection slot34 slot35)
		(pole_region pole1 slot12)
		(pole_region pole1 slot7)
		(forward_slot_connection slot30 slot31)
		(forward_slot_connection slot19 slot20)
		(forward_slot_connection slot5 slot6)
		(pole_region pole3 slot28)
		(forward_slot_connection slot25 slot26)
		(pole_available pole3)
		(pole_region pole3 slot32)
		(pole_region pole1 slot11)
		(forward_slot_connection slot7 slot8)
		(inverse_slot_connection slot24 slot23)
		(pole_region pole2 slot26)
		(pole_stop_moving pole1)
		(pole_region pole2 slot14)
		(inverse_slot_connection slot19 slot18)
		(pole_region pole2 slot20)
		(pole_region pole1 slot15)
		(slot_have_pole slot9)
		(forward_slot_connection slot13 slot14)
		(pole_region pole3 slot31)
		(inverse_slot_connection slot37 slot36)
		(pole_region pole3 slot38)
		(inverse_slot_connection slot16 slot15)
		(forward_slot_connection slot12 slot13)
		(forward_slot_connection slot10 slot11)
		(forward_slot_connection slot26 slot27)
		(pole_region pole1 slot9)
		(inverse_slot_connection slot13 slot12)
		(inverse_slot_connection slot6 slot5)
		(pole_region pole2 slot27)
		(pole_stop_moving pole2)
		(inverse_slot_connection slot4 slot3)
		(= (pole_start_duration) 2)
		(= (pole_hangoff_duration) 10)
		(stocking_slot slot1)
		(inverse_slot_connection slot23 slot22)
		(inverse_slot_connection slot3 slot2)
		(pole_region pole2 slot18)
		(pole_region pole2 slot29)
		(pole_region pole3 slot34)
		(forward_slot_connection slot33 slot34)
		(pole_region pole3 slot39)
		(inverse_slot_connection slot14 slot13)
		(forward_slot_connection slot18 slot19)
		(border_slot slot1)
		(forward_slot_connection slot6 slot7)
		(inverse_slot_connection slot26 slot25)
		(forward_slot_connection slot8 slot9)
		(forward_slot_connection slot2 slot3)
		(inverse_slot_connection slot21 slot20)
		(pole_region pole1 slot14)
		(pole_empty pole2)
		(inverse_slot_connection slot9 slot8)
		(inverse_slot_connection slot22 slot21)
		(blanking_slot slot1)
		(inverse_slot_connection slot8 slot7)
		(pole_position pole2 slot24)
		(pole_region pole3 slot29)
		(pole_region pole2 slot22)
		(pole_region pole2 slot21)
		(pole_available pole2)
		(pole_region pole3 slot35)
		(pole_region pole1 slot10)
		(forward_slot_connection slot3 slot4)
		(pole_region pole1 slot1)
		(inverse_slot_connection slot10 slot9)
		(slot_not_available slot38)
		(forward_slot_connection slot35 slot36)
		(pole_position pole3 slot38)
		(forward_slot_connection slot11 slot12)
		(pole_empty pole1)
		(inverse_slot_connection slot30 slot29)
		(inverse_slot_connection slot15 slot14)
		(pole_region pole3 slot37)
		(pole_region pole1 slot2)
		(product_at p0 slot38)
		(pole_available pole1)
		(forward_slot_connection slot32 slot33)
		(inverse_slot_connection slot7 slot6)
		(pole_region pole3 slot30)
		(pole_region pole1 slot4)
		(inverse_slot_connection slot28 slot27)
		(forward_slot_connection slot23 slot24)
		(forward_slot_connection slot36 slot37)
		(inverse_slot_connection slot31 slot30)
		(pole_region pole1 slot8)
		(forward_slot_connection slot29 slot30)
		(pole_region pole3 slot33)
		(pole_stop_moving pole3)
		(= (pole_moving_duration_each_slot) 1)
		(forward_slot_connection slot20 slot21)
		(border_slot slot39)
		(pole_region pole1 slot13)
		(pole_region pole2 slot19)
		(pole_region pole2 slot17)
		(forward_slot_connection slot14 slot15)
		(forward_slot_connection slot38 slot39)
		(inverse_slot_connection slot34 slot33)
		(inverse_slot_connection slot35 slot34)
		(forward_slot_connection slot27 slot28)
		(inverse_slot_connection slot12 slot11)
		(forward_slot_connection slot21 slot22)
		(inverse_slot_connection slot27 slot26)
		(inverse_slot_connection slot39 slot38)
		(forward_slot_connection slot28 slot29)
		(= (pole_hangon_duration) 10)
		(inverse_slot_connection slot38 slot37)
		(inverse_slot_connection slot2 slot1)
		(pole_position pole1 slot9)
		(pole_region pole1 slot5)
		(forward_slot_connection slot15 slot16)
		(forward_slot_connection slot16 slot17)
		(slot_have_pole slot24)
		(forward_slot_connection slot22 slot23)
		(inverse_slot_connection slot29 slot28)
		(forward_slot_connection slot17 slot18)
		(forward_slot_connection slot1 slot2)
		(pole_region pole2 slot23)
		(inverse_slot_connection slot5 slot4)
		(pole_region pole2 slot24)
		(pole_region pole2 slot15)
		(forward_slot_connection slot37 slot38)
		(pole_region pole1 slot3)
		(inverse_slot_connection slot36 slot35)
		(pole_region pole1 slot6)
		(pole_region pole2 slot25)
		(forward_slot_connection slot4 slot5)
		(inverse_slot_connection slot18 slot17)
		(inverse_slot_connection slot32 slot31)
		(inverse_slot_connection slot33 slot32)
		(pole_region pole3 slot36)
		(forward_slot_connection slot24 slot25)
		(forward_slot_connection slot9 slot10)
		(pole_region pole2 slot28)
		(slot_have_pole slot38)
		(inverse_slot_connection slot17 slot16)
		(inverse_slot_connection slot11 slot10)
		(inverse_slot_connection slot20 slot19)
	)
	(:goal
	(and
		(pole_have_things pole3 p0)
	)
	)
)
