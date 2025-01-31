'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import POI_FORM from './Add_poi_form';

export default function Show_prev_POIs({ poi_id, set_poi_id }) {

    const [pois, set_pois] = useState([]);
    const [show_poi_form, set_show_poi_form] = useState(false);

    useEffect(() => {
        async function get_pois() {
            try {
                const response = await fetch('/api/get_all_pois');
                if (!response.ok) throw new Error("Failed to fetch POIs");
                const data = await response.json();
                set_pois(data);
            } catch (error) {
                console.error("ERROR:", error);
            }
        }
        get_pois();
    }, [show_poi_form]);

    return (
        <div className=" w-[30vw] relative h-[82vh] flex flex-col">

            {/* SELECTED POI */}
            <>
                <div className=' text-2xl pb-3 '>
                    {
                        poi_id !== null ?
                            'Selected POI' :
                            'No POI Selected'
                    }
                </div>
                <div>
                    {
                        pois.map((val, idx) => {
                            // console.log(poi_id, val._id)
                            if (poi_id === val._id) {

                                return (
                                    <div onClick={() => { set_poi_id(val._id) }} key={idx} className=' px-4 py-2 flex items-center justify-between shadow shadow-primary transition-all  rounded-xl '>
                                        <div className=' flex items-center gap-5'>
                                            <div className=' rounded-full overflow-hidden'>
                                                <Image src={val.img_url} height={60} width={60} alt='NO img' />
                                            </div>
                                            <div className=' text-lg'>
                                                {val.name}
                                            </div>
                                        </div>
                                    </div>
                                )
                            }
                        })
                    }
                </div>
            </>

            {/* ALL POIS */}
            <>
                <div className=' text-xl pt-5 pb-4'>
                    People Of Interest (POIs)
                </div>
                <div className='py-3 px-1 overflow-y-auto mb-6'>
                    {
                        pois.map((val, idx) => {
                            // console.log(poi_id, val._id)
                            return (
                                <div onClick={() => { set_poi_id(val._id) }} key={idx} className=' cursor-pointer px-4 py-2 flex items-center justify-between shadow-sm shadow-white hover:shadow-primary transition-all  rounded-xl '>

                                    <div className=' flex items-center gap-5'>
                                        <div className=' rounded-full overflow-hidden'>
                                            <Image src={val.img_url} height={60} width={60} alt='NO img' />
                                        </div>
                                        <div className=' text-lg'>
                                            {val.name}
                                        </div>
                                    </div>
                                    {
                                        val._id === poi_id &&
                                        <div className='bg-primary text-white px-4 rounded-full ' >
                                            Selected
                                        </div>
                                    }
                                </div>
                            )
                        })
                    }
                </div>
            </>

            <div className={` ${show_poi_form ? "opacity-100 z-20 " : "opacity-0 h-0"} overflow-hidden absolute top-0 left-[105%] w-96 bg-white shadow-md shadow-primary rounded-2xl transition-all duration-300 `}>
                <div className=' p-6'>

                    <div onClick={() => { set_show_poi_form(false) }} className='  bg-red-200 hover:bg-red-500 w-fit p-2 rounded-full cursor-pointer absolute left-[85%] top-5 transition-all duration-300'>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                        </svg>

                    </div>
                    <POI_FORM set_show_poi_form={set_show_poi_form} />
                </div>
            </div>
            {
                show_poi_form === false &&
                <div onClick={() => { set_show_poi_form(true) }} className=' bg-primary text-white px-10 py-2 w-fit rounded-full  mx-auto cursor-pointer'>
                    Add Person
                </div>
            }

        </div>
    )
}