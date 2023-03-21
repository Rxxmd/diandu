(define (problem electroplating)
	(:domain Electroplating)
	(:objects
		slot1 - slot
		slot2 - slot
		slot3 - slot
		slot10 - slot
		slot11 - slot
		slot12 - slot
		pole1 - pole
		pole2 - pole
		gear1 - pole
		gear2 - pole
		p100000 - product
		p0 - product
		p1 - product
		p2 - product
		)
	(:init
		(pole_region pole2 slot10)
		(border_slot slot12)
		(exchanging_connection slot10 slot3)
		(exchanging_slot slot12)
		(border_slot slot1)
		(slot_have_pole slot3)
		(pole_region gear2 slot12)
		(slot_not_available slot10)
		(inverse_slot_connection slot11 slot10)
		(pole_region gear2 slot1)
		(exchanging_slot slot1)
		(forward_slot_connection slot11 slot12)
		(pole_have_things gear2 p0)
		(inverse_slot_connection slot12 slot11)
		(pole_empty pole1)
		(pole_stop_moving pole1)
		(product_at p0 slot12)
		(forward_slot_connection slot1 slot2)
		(pole_available gear2)
		(pole_position gear2 slot12)
		(pole_position gear1 slot3)
		(product_at p1 slot1)
		(pole_available pole1)
		(border_slot slot10)
		(pole_region pole1 slot3)
		(exchanging_slot slot10)
		(inverse_slot_connection slot3 slot2)
		(pole_region pole1 slot2)
		(exchanging_connection slot12 slot1)
		(slot_have_pole slot12)
		(border_slot slot3)
		(pole_region pole2 slot11)
		(exchanging_slot slot3)
		(= (pole_hangon_duration) 10)
		(pole_empty gear1)
		(forward_slot_connection slot10 slot11)
		(= (gear_moving_duration) 16)
		(exchanging_connection slot3 slot10)
		(pole_region pole2 slot12)
		(= (pole_hangoff_duration) 10)
		(pole_available gear1)
		(blanking_slot slot1)
		(stocking_slot slot1)
		(= (pole_start_duration) 2)
		(forward_slot_connection slot3 slot10)
		(exchanging_connection slot1 slot12)
		(slot_not_available slot12)
		(pole_stop_moving pole2)
		(pole_region gear1 slot10)
		(pole_empty pole2)
		(pole_position pole1 slot3)
		(pole_position pole2 slot12)
		(forward_slot_connection slot2 slot3)
		(product_at p2 slot1)
		(inverse_slot_connection slot10 slot3)
		(inverse_slot_connection slot2 slot1)
		(pole_available pole2)
		(= (pole_moving_duration_each_slot) 1)
		(pole_region pole1 slot1)
		(pole_region gear1 slot3)
	)
	(:goal
	(and
		(product_at p0 slot1)
	)
	)
)
