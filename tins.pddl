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
		p1 - product
		p2 - product
		p3 - product
		p4 - product
		p5 - product
		p6 - product
		p7 - product
		p8 - product
		p9 - product
		p10 - product
		p11 - product
		p12 - product
		p13 - product
		p14 - product
		p15 - product
		p16 - product
		p17 - product
		p18 - product
		p19 - product
		p20 - product
		p21 - product
		p22 - product
		p23 - product
		p24 - product
		p25 - product
		p26 - product
		p27 - product
		p28 - product
		p29 - product
		p30 - product
		p31 - product
		p32 - product
		p33 - product
		p34 - product
		p35 - product
		p36 - product
		p37 - product
		p38 - product
		)
	(:init
		(forward_slot_connection slot36 slot37)
		(pole_region pole1 slot10)
		(inverse_slot_connection slot36 slot35)
		(forward_slot_connection slot1 slot2)
		(pole_stop_moving pole2)
		(product_at p20 slot1)
		(inverse_slot_connection slot31 slot30)
		(product_at p21 slot1)
		(pole_position pole2 slot22)
		(inverse_slot_connection slot19 slot18)
		(product_at p31 slot1)
		(product_at p16 slot1)
		(product_at p2 slot1)
		(pole_position pole3 slot35)
		(border_slot slot39)
		(pole_region pole2 slot23)
		(slot_not_available slot8)
		(slot_not_available slot19)
		(pole_region pole3 slot38)
		(pole_region pole2 slot15)
		(product_at p18 slot1)
		(inverse_slot_connection slot3 slot2)
		(forward_slot_connection slot7 slot8)
		(inverse_slot_connection slot6 slot5)
		(product_at p35 slot1)
		(product_at p26 slot1)
		(inverse_slot_connection slot25 slot24)
		(pole_region pole1 slot2)
		(inverse_slot_connection slot28 slot27)
		(inverse_slot_connection slot30 slot29)
		(forward_slot_connection slot2 slot3)
		(= (gear_moving_duration) 16)
		(product_at p15 slot1)
		(product_at p19 slot1)
		(forward_slot_connection slot32 slot33)
		(pole_region pole1 slot8)
		(inverse_slot_connection slot34 slot33)
		(product_at p12 slot1)
		(forward_slot_connection slot28 slot29)
		(product_at p1 slot1)
		(slot_not_available slot14)
		(inverse_slot_connection slot13 slot12)
		(pole_available pole3)
		(pole_stop_moving pole3)
		(product_at p38 slot1)
		(forward_slot_connection slot24 slot25)
		(= (pole_hangoff_duration) 10)
		(forward_slot_connection slot23 slot24)
		(inverse_slot_connection slot35 slot34)
		(inverse_slot_connection slot39 slot38)
		(forward_slot_connection slot11 slot12)
		(pole_region pole2 slot17)
		(pole_region pole3 slot35)
		(product_at p33 slot1)
		(inverse_slot_connection slot17 slot16)
		(forward_slot_connection slot37 slot38)
		(forward_slot_connection slot3 slot4)
		(pole_available pole2)
		(inverse_slot_connection slot4 slot3)
		(product_at p29 slot1)
		(forward_slot_connection slot31 slot32)
		(pole_region pole2 slot22)
		(pole_region pole1 slot14)
		(pole_region pole3 slot39)
		(product_at p36 slot1)
		(pole_region pole1 slot12)
		(forward_slot_connection slot15 slot16)
		(pole_region pole3 slot33)
		(inverse_slot_connection slot23 slot22)
		(blanking_slot slot1)
		(inverse_slot_connection slot5 slot4)
		(product_at p22 slot1)
		(product_at p32 slot1)
		(forward_slot_connection slot25 slot26)
		(product_at p34 slot1)
		(forward_slot_connection slot5 slot6)
		(pole_region pole3 slot31)
		(forward_slot_connection slot20 slot21)
		(pole_region pole2 slot28)
		(product_at p24 slot1)
		(pole_region pole2 slot18)
		(forward_slot_connection slot27 slot28)
		(forward_slot_connection slot16 slot17)
		(pole_region pole2 slot25)
		(forward_slot_connection slot29 slot30)
		(pole_region pole3 slot29)
		(inverse_slot_connection slot12 slot11)
		(inverse_slot_connection slot8 slot7)
		(pole_region pole2 slot29)
		(forward_slot_connection slot9 slot10)
		(forward_slot_connection slot10 slot11)
		(forward_slot_connection slot18 slot19)
		(inverse_slot_connection slot9 slot8)
		(pole_stop_moving pole1)
		(forward_slot_connection slot34 slot35)
		(forward_slot_connection slot17 slot18)
		(pole_empty pole2)
		(product_at p23 slot1)
		(forward_slot_connection slot6 slot7)
		(pole_region pole2 slot26)
		(product_at p28 slot1)
		(product_at p17 slot1)
		(product_at p3 slot1)
		(forward_slot_connection slot30 slot31)
		(pole_region pole1 slot9)
		(slot_have_pole slot35)
		(forward_slot_connection slot19 slot20)
		(product_at p8 slot14)
		(slot_have_pole slot22)
		(product_at p11 slot1)
		(pole_region pole1 slot11)
		(pole_region pole1 slot13)
		(product_at p13 slot1)
		(forward_slot_connection slot13 slot14)
		(stocking_slot slot1)
		(product_at p25 slot1)
		(forward_slot_connection slot12 slot13)
		(border_slot slot1)
		(inverse_slot_connection slot2 slot1)
		(product_at p0 slot1)
		(product_at p14 slot1)
		(product_at p9 slot1)
		(forward_slot_connection slot4 slot5)
		(pole_region pole3 slot28)
		(forward_slot_connection slot14 slot15)
		(inverse_slot_connection slot21 slot20)
		(pole_region pole2 slot19)
		(forward_slot_connection slot35 slot36)
		(forward_slot_connection slot21 slot22)
		(pole_region pole1 slot1)
		(inverse_slot_connection slot33 slot32)
		(pole_region pole1 slot5)
		(inverse_slot_connection slot20 slot19)
		(= (pole_moving_duration_each_slot) 1)
		(product_at p37 slot1)
		(pole_empty pole3)
		(inverse_slot_connection slot14 slot13)
		(product_at p7 slot35)
		(slot_not_available slot35)
		(inverse_slot_connection slot38 slot37)
		(pole_available pole1)
		(pole_region pole1 slot6)
		(pole_region pole2 slot24)
		(pole_region pole2 slot20)
		(inverse_slot_connection slot24 slot23)
		(= (pole_hangon_duration) 10)
		(pole_region pole3 slot30)
		(pole_region pole1 slot3)
		(inverse_slot_connection slot15 slot14)
		(pole_region pole2 slot14)
		(forward_slot_connection slot8 slot9)
		(= (pole_start_duration) 2)
		(product_at p6 slot19)
		(inverse_slot_connection slot32 slot31)
		(inverse_slot_connection slot16 slot15)
		(pole_region pole3 slot37)
		(pole_region pole3 slot32)
		(forward_slot_connection slot26 slot27)
		(pole_region pole2 slot27)
		(inverse_slot_connection slot22 slot21)
		(inverse_slot_connection slot18 slot17)
		(inverse_slot_connection slot27 slot26)
		(pole_region pole1 slot4)
		(inverse_slot_connection slot29 slot28)
		(pole_region pole1 slot7)
		(pole_region pole3 slot36)
		(inverse_slot_connection slot37 slot36)
		(product_at p10 slot1)
		(pole_region pole2 slot16)
		(product_at p4 slot8)
		(product_at p5 slot12)
		(pole_region pole1 slot15)
		(pole_region pole3 slot34)
		(pole_position pole1 slot8)
		(product_at p30 slot1)
		(forward_slot_connection slot33 slot34)
		(pole_empty pole1)
		(forward_slot_connection slot38 slot39)
		(pole_region pole2 slot21)
		(forward_slot_connection slot22 slot23)
		(slot_have_pole slot8)
		(inverse_slot_connection slot7 slot6)
		(slot_not_available slot12)
		(inverse_slot_connection slot11 slot10)
		(inverse_slot_connection slot10 slot9)
		(inverse_slot_connection slot26 slot25)
		(product_at p27 slot1)
	)
	(:goal
	(and
		(pole_position pole3 slot34)
	)
	)
)
