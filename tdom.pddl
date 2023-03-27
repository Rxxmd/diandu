
    (define (domain Electroplating)
    (:requirements :typing :fluents :CONDITIONAL-EFFECTS :equality :durative-actions :negative-preconditions)
    (:types
        pole slot product - object
    )
    (:predicates

        (pole_position ?p - pole ?s - slot) ;pole ?p is at slot ?s
        (slot_have_pole ?s - slot)

        (pole_region ?p - pole ?s - slot) ;pole ?p is available to be at ?s
        (pole_have_things ?p - pole ?r - product) ;pole is hanging ?r
        (pole_empty ?p - pole) ;pole has nothing

        (pole_available ?p - pole)

        (product_at ?r - product ?s - slot)
        ; (product_craft ?r - product ?c - craft)
        (target_slot ?s - slot ?r - product)
        (gear_pole ?p - pole)

        (forward_slot_connection ?s1 - slot ?s2 - slot)
        (inverse_slot_connection ?s1 - slot ?s2 - slot)
        (exchanging_connection ?s1 - slot ?s2 - slot)
        (border_slot ?s - slot)

        ;(slot_setting ?s - slot ?o - process)
        (stocking_slot ?s - slot)
        (blanking_slot ?s - slot)
        (exchanging_slot ?s - slot)

        (slot_not_available ?s - slot)
        ;  (complete ?r - product)

        (pole_start_moving ?p - pole)
        (pole_stop_moving ?p - pole)

    )

    (:functions
        (procedure_executing ?r - product) ;How many procedures are executed?
        ;(procedure_craft ?o - process ?c - craft)
        ;(procedure_blanking ?c - craft)

        (pole_moving_duration_each_slot)
        (pole_stop_duration)
        (pole_start_duration)
        (pole_hangon_duration)
        (pole_hangoff_duration)
        (gear_moving_duration)

        ;(procedure_duration ?o - process ?c - craft)
    )

    ;;;;;;;;;;;;;;;;;;;  Actions About Poles ;;;;;;;;;;;;;;;;;;;;;;

    (:durative-action Start-Moving-Pole
        :parameters (?p - pole)
        :duration (= ?duration (pole_start_duration))
        :condition ( and (at start (pole_stop_moving ?p))
            (at start(pole_available ?p))
        )
        :effect (and (at end (pole_start_moving ?p))
            (at start (not (pole_stop_moving ?p)))
            (at start (not (pole_available ?p)))
            (at end (pole_available ?p))
        )
    )
    
                (:durative-action Move-Pole-forward-1
                :parameters (?p - pole ?s1 - slot ?s2 - slot ?s3 - slot ?s4 - slot ?s5 - slot ?s6 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    
                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (forward_slot_connection ?s1 ?s2))
(over all (forward_slot_connection ?s2 ?s3))
(over all (forward_slot_connection ?s3 ?s4))
(over all (forward_slot_connection ?s4 ?s5))
(over all (forward_slot_connection ?s5 ?s6))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))
(over all (not (slot_have_pole ?s3)))
(over all (not (slot_have_pole ?s4)))
(over all (not (slot_have_pole ?s5)))
(over all (not (slot_have_pole ?s6)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))(at start (slot_have_pole ?s3))(at start (slot_have_pole ?s4))(at start (slot_have_pole ?s5))(at start (slot_have_pole ?s6))
                    (at end (not (slot_have_pole ?s1)))
(at end (not (slot_have_pole ?s3)))
(at end (not (slot_have_pole ?s4)))
(at end (not (slot_have_pole ?s5)))
(at end (not (slot_have_pole ?s6)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
                (:durative-action Move-Pole-forward-2
                :parameters (?p - pole ?s1 - slot ?s2 - slot ?s3 - slot ?s4 - slot ?s5 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    (over all(border_slot ?s5))

                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (forward_slot_connection ?s1 ?s2))
(over all (forward_slot_connection ?s2 ?s3))
(over all (forward_slot_connection ?s3 ?s4))
(over all (forward_slot_connection ?s4 ?s5))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))
(over all (not (slot_have_pole ?s3)))
(over all (not (slot_have_pole ?s4)))
(over all (not (slot_have_pole ?s5)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))(at start (slot_have_pole ?s3))(at start (slot_have_pole ?s4))(at start (slot_have_pole ?s5))
                    (at end (not (slot_have_pole ?s1)))
(at end (not (slot_have_pole ?s3)))
(at end (not (slot_have_pole ?s4)))
(at end (not (slot_have_pole ?s5)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
                (:durative-action Move-Pole-forward-3
                :parameters (?p - pole ?s1 - slot ?s2 - slot ?s3 - slot ?s4 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    (over all(border_slot ?s4))

                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (forward_slot_connection ?s1 ?s2))
(over all (forward_slot_connection ?s2 ?s3))
(over all (forward_slot_connection ?s3 ?s4))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))
(over all (not (slot_have_pole ?s3)))
(over all (not (slot_have_pole ?s4)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))(at start (slot_have_pole ?s3))(at start (slot_have_pole ?s4))
                    (at end (not (slot_have_pole ?s1)))
(at end (not (slot_have_pole ?s3)))
(at end (not (slot_have_pole ?s4)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
                (:durative-action Move-Pole-forward-4
                :parameters (?p - pole ?s1 - slot ?s2 - slot ?s3 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    (over all(border_slot ?s3))

                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (forward_slot_connection ?s1 ?s2))
(over all (forward_slot_connection ?s2 ?s3))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))
(over all (not (slot_have_pole ?s3)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))(at start (slot_have_pole ?s3))
                    (at end (not (slot_have_pole ?s1)))
(at end (not (slot_have_pole ?s3)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
                (:durative-action Move-Pole-forward-5
                :parameters (?p - pole ?s1 - slot ?s2 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    (over all(border_slot ?s2))

                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (forward_slot_connection ?s1 ?s2))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))
                    (at end (not (slot_have_pole ?s1)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
                (:durative-action Move-Pole-inverse-1
                :parameters (?p - pole ?s1 - slot ?s2 - slot ?s3 - slot ?s4 - slot ?s5 - slot ?s6 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    
                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (inverse_slot_connection ?s1 ?s2))
(over all (inverse_slot_connection ?s2 ?s3))
(over all (inverse_slot_connection ?s3 ?s4))
(over all (inverse_slot_connection ?s4 ?s5))
(over all (inverse_slot_connection ?s5 ?s6))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))
(over all (not (slot_have_pole ?s3)))
(over all (not (slot_have_pole ?s4)))
(over all (not (slot_have_pole ?s5)))
(over all (not (slot_have_pole ?s6)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))(at start (slot_have_pole ?s3))(at start (slot_have_pole ?s4))(at start (slot_have_pole ?s5))(at start (slot_have_pole ?s6))
                    (at end (not (slot_have_pole ?s1)))
(at end (not (slot_have_pole ?s3)))
(at end (not (slot_have_pole ?s4)))
(at end (not (slot_have_pole ?s5)))
(at end (not (slot_have_pole ?s6)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
                (:durative-action Move-Pole-inverse-2
                :parameters (?p - pole ?s1 - slot ?s2 - slot ?s3 - slot ?s4 - slot ?s5 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    (over all(border_slot ?s5))

                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (inverse_slot_connection ?s1 ?s2))
(over all (inverse_slot_connection ?s2 ?s3))
(over all (inverse_slot_connection ?s3 ?s4))
(over all (inverse_slot_connection ?s4 ?s5))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))
(over all (not (slot_have_pole ?s3)))
(over all (not (slot_have_pole ?s4)))
(over all (not (slot_have_pole ?s5)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))(at start (slot_have_pole ?s3))(at start (slot_have_pole ?s4))(at start (slot_have_pole ?s5))
                    (at end (not (slot_have_pole ?s1)))
(at end (not (slot_have_pole ?s3)))
(at end (not (slot_have_pole ?s4)))
(at end (not (slot_have_pole ?s5)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
                (:durative-action Move-Pole-inverse-3
                :parameters (?p - pole ?s1 - slot ?s2 - slot ?s3 - slot ?s4 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    (over all(border_slot ?s4))

                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (inverse_slot_connection ?s1 ?s2))
(over all (inverse_slot_connection ?s2 ?s3))
(over all (inverse_slot_connection ?s3 ?s4))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))
(over all (not (slot_have_pole ?s3)))
(over all (not (slot_have_pole ?s4)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))(at start (slot_have_pole ?s3))(at start (slot_have_pole ?s4))
                    (at end (not (slot_have_pole ?s1)))
(at end (not (slot_have_pole ?s3)))
(at end (not (slot_have_pole ?s4)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
                (:durative-action Move-Pole-inverse-4
                :parameters (?p - pole ?s1 - slot ?s2 - slot ?s3 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    (over all(border_slot ?s3))

                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (inverse_slot_connection ?s1 ?s2))
(over all (inverse_slot_connection ?s2 ?s3))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))
(over all (not (slot_have_pole ?s3)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))(at start (slot_have_pole ?s3))
                    (at end (not (slot_have_pole ?s1)))
(at end (not (slot_have_pole ?s3)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
                (:durative-action Move-Pole-inverse-5
                :parameters (?p - pole ?s1 - slot ?s2 - slot )
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    (over all(border_slot ?s2))

                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    (over all (inverse_slot_connection ?s1 ?s2))

                    (at start (slot_have_pole ?s1))
                    (over all (not (slot_have_pole ?s2)))

                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    (at start (slot_have_pole ?s1))(at start (slot_have_pole ?s2))
                    (at end (not (slot_have_pole ?s1)))

                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            
    (:durative-action Move-Gear-equip
        :parameters (?p - pole ?s1 - slot ?s2 - slot ?r - product)
        :duration (= ?duration (gear_moving_duration))
        :condition ( and (over all(exchanging_connection ?s1 ?s2))
            (over all(exchanging_slot ?s1))
            (over all(exchanging_slot ?s2))
            (at start(pole_position ?p ?s1))
            ; (at start(slot_have_pole ?s1))
            ; (at start (not (slot_have_pole ?s2)))
            (at start (not (pole_empty ?p)))

            (at start (product_at ?r ?s1))

            (at start (slot_not_available ?s1))
            (over all(pole_region ?p ?s1))
            (over all(pole_region ?p ?s2))

            (at start(pole_available ?p))
        )
        :effect (and (at start(not (pole_position ?p ?s1)))
            (at end(pole_position ?p ?s2))

            (at start (not (product_at ?r ?s1)))
            (at end (product_at ?r ?s2))

            (at start (slot_not_available ?s1))
            (at end (slot_not_available ?s2))

            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))

            (at end(not (target_slot ?s2 ?r)))
        )
    )

    (:durative-action Move-Gear-empty
        :parameters (?p - pole ?s1 - slot ?s2 - slot)
        :duration (= ?duration (gear_moving_duration))
        :condition ( and (over all(exchanging_connection ?s1 ?s2))
            (over all(exchanging_slot ?s1))
            (over all(exchanging_slot ?s2))
            (at start(pole_position ?p ?s1))

            (at start (slot_not_available ?s2))

            (over all(pole_empty ?p))
            (over all(pole_region ?p ?s1))
            (over all(pole_region ?p ?s2))
            (at start(pole_available ?p))
        )
        :effect (and (at start(not (pole_position ?p ?s1)))
            (at end(pole_position ?p ?s2))

            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))

            (at start (slot_not_available ?s1))
            (at end (not (slot_not_available ?s2)))
        )
    )
    (:durative-action HangUp-Pole
        :parameters (?p - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangon_duration))
        :condition (and (at start(pole_empty ?p))
            
            ;(at start(product_available ?r))
            (at start(product_at ?r ?s))
            (over all(pole_position ?p ?s))
            (at start (pole_available ?p))
            (at start(slot_not_available ?s))
            (over all(not(stocking_slot ?s)))
            (over all(not(exchanging_slot ?s)))
        )
        :effect (and (at start(not (pole_empty ?p)))
            ;(at start(not (product_available ?r)))
            (at start (not (product_at ?r ?s)))
            (at end (pole_have_things ?p ?r))
            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))
            (at end(not (slot_not_available ?s)))
        )
    )

    (:durative-action HangUp-Pole-exchanging
        :parameters (?p - pole ?g - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangon_duration))
        :condition (and (at start(pole_empty ?p))
            (at start(not (pole_empty ?g)))
            ;(at start(product_available ?r))
            (at start(product_at ?r ?s))
            (over all(pole_position ?p ?s))
            (over all(pole_position ?g ?s))

            (at start (pole_available ?p))
            (at start (pole_available ?g))

            (at start(slot_not_available ?s))

            (over all(not(stocking_slot ?s)))
            (over all(exchanging_slot ?s))

            (over all (not (gear_pole ?p)))
        )
        :effect (and (at start(not (pole_empty ?p)))
            (at end (pole_empty ?g))

            (at start (not (product_at ?r ?s)))

            (at end (pole_have_things ?p ?r))
            (at start (not (pole_have_things ?g ?r)))

            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))

            (at start(not (pole_available ?g)))
            (at end(pole_available ?g))

            (at end(not (slot_not_available ?s)))
        )
    )

    (:durative-action HangUp-Pole-stocking
        :parameters (?p - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangon_duration))
        :condition (and (at start(pole_empty ?p))
            ;(at start(product_available ?r))
            (at start(product_at ?r ?s))
            (over all(pole_position ?p ?s))
            (at start (pole_available ?p))
            (over all(stocking_slot ?s))
        )
        :effect (and (at start(not (pole_empty ?p)))
            ;(at start(not (product_available ?r)))
            (at start (not (product_at ?r ?s)))
            (at end (pole_have_things ?p ?r))
            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))
        )
    )

    (:durative-action HangOff-Pole
        :parameters (?p - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangoff_duration))
        :condition (and (at start(pole_have_things ?p ?r))
            (over all(pole_position ?p ?s))
            (at start (pole_available ?p))
            (over all (target_slot ?s ?r))
            (at start (not (slot_not_available ?s)))
            (over all (not (blanking_slot ?s)))
            (over all (not (exchanging_slot ?s)))
        )
        :effect (and (at end(pole_empty ?p))
            (at end(product_at ?r ?s))
            (at end(not (pole_have_things ?p ?r)))
            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))
            (at end(not (target_slot ?s ?r)))
            (at start (slot_not_available ?s))
        )
    )

    (:durative-action HangOff-Pole-blanking
        :parameters (?p - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangoff_duration))
        :condition (and (at start(pole_have_things ?p ?r))
            (over all(pole_position ?p ?s))
            (at start (pole_available ?p))
            (over all (target_slot ?s ?r))
            (over all (blanking_slot ?s))
        )
        :effect (and (at end(pole_empty ?p))
            (at end(product_at ?r ?s))
            (at end(not (pole_have_things ?p ?r)))
            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))
            (at end(not (target_slot ?s ?r)))
        )
    )

    (:durative-action HangOff-Pole-exchanging
        :parameters (?p - pole ?g - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangoff_duration))
        :condition (and (at start(pole_have_things ?p ?r))
            (over all(pole_position ?p ?s))
            (over all(pole_position ?g ?s))

            (at start (pole_available ?p))
            (at start (pole_available ?g))

            (over all (target_slot ?s ?r))
            (at start (not (slot_not_available ?s)))
            (over all (exchanging_slot ?s))

            (over all (not (gear_pole ?p)))
        )
        :effect (and (at end(pole_empty ?p))
            (at end(not (pole_empty ?g)))

            (at end(product_at ?r ?s))
            (at start (slot_not_available ?s))

            (at end(not (pole_have_things ?p ?r)))
            (at end(pole_have_things ?g ?r))

            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))

            (at start(not (pole_available ?g)))
            (at end(pole_available ?g))

            (at end(not (target_slot ?s ?r)))
        )
    )
    )
