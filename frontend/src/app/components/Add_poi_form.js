'use client'

import { useState, useRef } from 'react'
import Image from 'next/image'
import { save_poi, create_s3_save_url } from "@/lib/data";

export default function POI_FORM({ set_show_poi_form }) {

    const [name, setName] = useState('')
    const [files, setFiles] = useState([])
    const [isDragActive, setIsDragActive] = useState(false)
    const [loading, setloading] = useState(false);
    // let poi_mongo_id = null;
    //   const [state, formAction] = useActionState(saveData)
    const fileInputRef = useRef(null)

    const handleDragEnter = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragActive(true)
    }

    const handleDragLeave = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragActive(false)
    }

    const handleDragOver = (e) => {
        e.preventDefault()
        e.stopPropagation()
    }

    const handleDrop = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragActive(false)

        const droppedFiles = Array.from(e.dataTransfer.files)
        setFiles(prevFiles => [...prevFiles, ...droppedFiles])
    }

    const handleFileChange = (e) => {
        if (e.target.files) {
            const selectedFiles = Array.from(e.target.files)
            setFiles(prevFiles => [...prevFiles, ...selectedFiles])
        }
    }

    const removeFile = (index) => {
        setFiles(prevFiles => prevFiles.filter((_, i) => i !== index))
    }

    // SUBMIT RELATED FUNCTIONS

    const upload_file_s3 = async (file_idx, signedUrl) => {
        try {
            const file = files[file_idx];
            //send file to save 
            const res_s3 = await fetch(signedUrl, {
                method: 'PUT',
                body: file,
                headers: { 'Content-Type': file.type },
            });
            return 0;
        } catch (error) {
            console.error('Error uploading file:', error);
            return 1;
        }
    }

    const handle_submit = async (e) => {
        e.preventDefault()

        setloading(true)
        // save to POI collection in mongodb
        // name, S3 keys of all poi images
        try {

            // create poi_data
            let poi_data = {
                "name": name,
                "s3_keys": []
            }
            // create a mongodb_doc
            const res = await save_poi(poi_data);
            if (typeof (res) === 'number') {
                throw "error in creating doc"
            }

            const mongo_id = res;
            poi_data["mongo_id"] = mongo_id;

            //save to S3
            for (let i = 0; i < files.length; i++) {
                const s3_key = `POI/${mongo_id}_${name}/file_${i}`;
                poi_data["s3_keys"].push(s3_key);

                //create a signed URL for it
                const signed_url = await create_s3_save_url(s3_key, files[i].type);
                // save file using a put request
                const response = await upload_file_s3(i, signed_url);
                if (response === 1) {
                    throw "error in saving a file";
                }
            }
            console.log("before update POI data: ", poi_data)
            const update_res = await save_poi(poi_data);
            alert("files saved sucessfully !");
            setloading(false)
            //Redirect to crawl-sites with the POI-id
            // router.push(`/crawl-sites?poi=${mongo_id}`);
            set_show_poi_form(false)
        }
        catch (error) {
            console.error("Error in saving files: ", error);
            alert('Failed to upload files');
            setloading(false)
        }
    }

    return (
        <>
            <div className=' pb-8 gap-2 flex flex-col'>
                <div className=' text-xl font-semibold'>
                    Add Person of Interest
                </div>
                <div className='text-sm'>
                    Enter details of the person for recognition
                </div>
            </div>
            <form onSubmit={handle_submit} className="space-y-6">
                <div className=' flex items-center gap-5'>
                    <label htmlFor="name">Name</label>
                    <input
                        id="name"
                        name="name"
                        value={name}
                        placeholder='Name of the PoI..'
                        className='outline-gray-400 px-3 py-2 border-2 rounded-lg w-full'
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>

                <div>
                    <label htmlFor="images">Images</label>
                    <div
                        className={`p-6 mt-2 group border-2 border-dashed rounded-md cursor-pointer ${isDragActive ? 'border-primary' : 'border-gray-300'
                            }`}
                        onDragEnter={handleDragEnter}
                        onDragLeave={handleDragLeave}
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            id="images"
                            name="images"
                            accept="image/*"
                            multiple
                            onChange={handleFileChange}
                            className="hidden"
                            required
                        />
                        <div className=' flex flex-col items-center gap-2'>
                            <span className=' group-hover:-translate-y-1 transition-all'>
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-6">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                                </svg>
                            </span>
                            <p className="text-center ">
                                {isDragActive ? "Drop the files here ..." : "Drag 'n' drop the POI's images here, or click to select files"}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="space-y-2">
                    {files.map((file, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-100 rounded">
                            <div className="flex items-center space-x-2">
                                <Image
                                    src={URL.createObjectURL(file)}
                                    alt={`Uploaded image ${index + 1}`}
                                    width={40}
                                    height={40}
                                    className="rounded"
                                />
                                <span>{file.name}</span>
                            </div>
                            <button
                                type="button"
                                className='mx-4 hover:bg-red-300 p-2 rounded-full bg-slate-300 transition-all'
                                onClick={() => removeFile(index)}
                                aria-label={`Remove ${file.name}`}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" className="size-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14" />
                                </svg>

                            </button>
                        </div>
                    ))}
                </div>

                <button type="submit" className="w-full bg-primary text-slate-200 py-2 rounded-full hover:opacity-95 flex items-center justify-center gap-5">
                    <span>
                        Save
                    </span>
                    {loading &&
                        (
                            <div role="status">
                                {/* LOADING */}
                                <svg aria-hidden="true" className="w-4 h-4  animate-spin fill-primary" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor" />
                                    <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill" />
                                </svg>
                            </div>
                        )
                    }
                </button>
            </form>

        </>
    )
}